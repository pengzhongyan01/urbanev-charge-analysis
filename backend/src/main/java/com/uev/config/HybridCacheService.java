package com.uev.config;

import com.uev.vo.CacheStatsVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;

import java.util.Iterator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 双模缓存实现 —— D07（Redis 缓存）与 D13（异常降级证据）。
 *
 * <p>工作方式：
 * <ol>
 *   <li>优先走 Redis，key 带 TTL；</li>
 *   <li>Redis 抛任何异常（连不上 / 超时 / 密码错）→ 立刻标记 {@code redisBroken=true}，
 *       打一条 WARN 日志说明"已降级为本地缓存"，之后所有请求直接走本地缓存，不再反复去连 Redis；</li>
 *   <li>本地缓存是带过期时间的 ConcurrentHashMap，容量到上限时按过期时间淘汰，
 *       保证降级后也不会把堆撑爆。</li>
 * </ol>
 *
 * <p>这段代码就是答辩时"系统可用性"那一页的证据：
 * 把 Redis 停掉，接口照样返回 200，只是第二次请求变慢，日志里能看到降级记录。
 *
 * @author 杨姗姗（D 岗）
 */
@Slf4j
public class HybridCacheService implements CacheService {

    private final StringRedisTemplate redisTemplate;
    private final Map<String, LocalEntry> localCache = new ConcurrentHashMap<>();
    private final int maxLocalSize;

    private volatile boolean redisEnabled;
    private volatile boolean redisBroken = false;

    private final AtomicLong hitCount = new AtomicLong();
    private final AtomicLong missCount = new AtomicLong();
    private final AtomicLong hitCostNanos = new AtomicLong();
    private final AtomicLong missCostNanos = new AtomicLong();

    public HybridCacheService(StringRedisTemplate redisTemplate, boolean redisEnabled, int maxLocalSize) {
        this.redisTemplate = redisTemplate;
        this.redisEnabled = redisEnabled && redisTemplate != null;
        this.maxLocalSize = Math.max(64, maxLocalSize);
    }

    @Override
    public String getRaw(String key) {
        if (useRedis()) {
            try {
                return redisTemplate.opsForValue().get(key);
            } catch (Exception e) {
                degrade("读取", e);
            }
        }
        LocalEntry entry = localCache.get(key);
        if (entry == null) {
            return null;
        }
        if (entry.expireAt > 0 && entry.expireAt < System.currentTimeMillis()) {
            localCache.remove(key);
            return null;
        }
        return entry.json;
    }

    @Override
    public void putRaw(String key, String json, int ttlSeconds) {
        if (json == null || ttlSeconds <= 0) {
            return;
        }
        if (useRedis()) {
            try {
                redisTemplate.opsForValue().set(key, json, ttlSeconds, TimeUnit.SECONDS);
                return;
            } catch (Exception e) {
                degrade("写入", e);
            }
        }
        if (localCache.size() >= maxLocalSize) {
            evict();
        }
        localCache.put(key, new LocalEntry(json, System.currentTimeMillis() + ttlSeconds * 1000L));
    }

    @Override
    public String type() {
        return useRedis() ? "redis" : "local";
    }

    @Override
    public int localEntries() {
        return useRedis() ? -1 : localCache.size();
    }

    @Override
    public boolean available() {
        if (!useRedis()) {
            return true; // 本地缓存永远可用
        }
        try {
            String pong = redisTemplate.getConnectionFactory().getConnection().ping();
            return pong != null;
        } catch (Exception e) {
            degrade("心跳检测", e);
            return true; // 已降级到本地，对上层仍算可用
        }
    }

    @Override
    public void recordHit(long costNanos) {
        hitCount.incrementAndGet();
        hitCostNanos.addAndGet(Math.max(0, costNanos));
    }

    @Override
    public void recordMiss(long costNanos) {
        missCount.incrementAndGet();
        missCostNanos.addAndGet(Math.max(0, costNanos));
    }

    @Override
    public CacheStatsVO stats() {
        CacheStatsVO vo = new CacheStatsVO();
        vo.setType(type());
        long hit = hitCount.get();
        long miss = missCount.get();
        vo.setHitCount(hit);
        vo.setMissCount(miss);
        vo.setHitRate(hit + miss == 0 ? 0.0 : round((double) hit / (hit + miss)));
        // 用纳秒累加再换算，避免命中耗时被四舍五入成 0，导致加速比算不出来
        double hitAvg = hit == 0 ? 0.0 : (double) hitCostNanos.get() / hit / 1_000_000.0;
        double missAvg = miss == 0 ? 0.0 : (double) missCostNanos.get() / miss / 1_000_000.0;
        vo.setHitAvgMs(round(hitAvg));
        vo.setMissAvgMs(round(missAvg));
        vo.setSpeedup(hitAvg <= 0 ? 0.0 : round(missAvg / hitAvg));
        vo.setLocalEntries(localEntries());
        return vo;
    }

    @Override
    public void resetStats() {
        hitCount.set(0);
        missCount.set(0);
        hitCostNanos.set(0);
        missCostNanos.set(0);
    }

    // ---------------------------------------------------------------- 内部方法

    private boolean useRedis() {
        return redisEnabled && !redisBroken;
    }

    private void degrade(String action, Exception e) {
        if (!redisBroken) {
            redisBroken = true;
            log.warn("[缓存降级] Redis {}失败（{}），已自动切换为本地缓存，接口不受影响",
                    action, e.getMessage());
        }
    }

    private void evict() {
        long now = System.currentTimeMillis();
        Iterator<Map.Entry<String, LocalEntry>> it = localCache.entrySet().iterator();
        int removed = 0;
        while (it.hasNext() && removed < maxLocalSize / 4) {
            Map.Entry<String, LocalEntry> e = it.next();
            if (e.getValue().expireAt > 0 && e.getValue().expireAt < now) {
                it.remove();
                removed++;
            }
        }
        if (removed == 0) {
            // 没有过期项就淘汰最早插入的一批，避免无界增长
            Object[] keys = localCache.keySet().toArray();
            for (int i = 0; i < Math.min(keys.length, maxLocalSize / 4); i++) {
                localCache.remove((String) keys[i]);
            }
        }
    }

    private double round(double v) {
        return Math.round(v * 1000.0) / 1000.0;
    }

    /** 本地缓存条目：JSON + 过期时间戳 */
    private static class LocalEntry {
        final String json;
        final long expireAt;

        LocalEntry(String json, long expireAt) {
            this.json = json;
            this.expireAt = expireAt;
        }
    }
}
