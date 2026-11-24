package com.uev.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.core.StringRedisTemplate;

/**
 * 缓存装配。
 *
 * <p>uev.cache.type 三种取值：
 * <ul>
 *   <li>{@code redis}：强制走 Redis，连不上就自动降级；</li>
 *   <li>{@code local}：强制走本地缓存（没有 Redis 的机器也能跑）；</li>
 *   <li>{@code auto}（默认）：先探活 Redis，通就走 Redis，不通就降级。</li>
 * </ul>
 *
 * @author 杨姗姗（D 岗）
 */
@Slf4j
@Configuration
public class CacheConfig {

    @Value("${uev.cache.type:auto}")
    private String cacheType;

    @Value("${uev.cache.local.max-size:2000}")
    private int maxLocalSize;

    @Bean
    public CacheService cacheService(ObjectProvider<StringRedisTemplate> redisProvider) {
        StringRedisTemplate redis = redisProvider.getIfAvailable();
        boolean wantRedis = !"local".equalsIgnoreCase(cacheType) && redis != null;

        boolean redisOk = false;
        if (wantRedis) {
            try {
                redis.getConnectionFactory().getConnection().ping();
                redisOk = true;
                log.info("[缓存] 模式={} → Redis 连接正常，启用 Redis 缓存", cacheType);
            } catch (Exception e) {
                log.warn("[缓存] Redis 探活失败（{}），已自动降级为本地缓存，接口不受影响", e.getMessage());
            }
        } else {
            log.info("[缓存] 模式={} → 使用本地缓存（无 Redis 依赖）", cacheType);
        }
        return new HybridCacheService(redis, redisOk, maxLocalSize);
    }
}
