package com.uev.config;

import com.uev.vo.CacheStatsVO;

/**
 * 缓存抽象 —— D07 / D13 的核心。
 *
 * <p>抽象的目的只有一个：<b>Redis 挂了系统不能挂</b>。
 * 所有缓存读写都走这个接口，实现类内部自己决定是走 Redis 还是本地，
 * Service / Controller 完全不需要知道当前用的是哪种缓存。
 *
 * @author 杨珊珊（D 岗）
 */
public interface CacheService {

    /** 取缓存原文（JSON 字符串），不存在返回 null */
    String getRaw(String key);

    /** 写缓存，ttlSeconds <= 0 表示不写 */
    void putRaw(String key, String json, int ttlSeconds);

    /** 当前实际生效的实现：redis / local */
    String type();

    /** 本地缓存条目数，redis 模式返回 -1 */
    int localEntries();

    /** 缓存是否真正可用（健康检查用） */
    boolean available();

    void recordHit(long costNanos);

    void recordMiss(long costNanos);

    CacheStatsVO stats();

    void resetStats();
}
