package com.uev.aspect;

/**
 * 本次请求是否命中缓存的 ThreadLocal —— 给 query_log 的 hit_cache 字段用。
 *
 * <p>用完必须 clear()，否则线程池复用时上一个请求的标记会串到下一个请求。
 *
 * @author 杨姗姗（D 岗）
 */
public final class CacheContext {

    private static final ThreadLocal<Boolean> HIT = new ThreadLocal<>();

    private CacheContext() {
    }

    public static void setHit(boolean hit) {
        HIT.set(hit);
    }

    public static boolean isHit() {
        return Boolean.TRUE.equals(HIT.get());
    }

    public static void clear() {
        HIT.remove();
    }
}
