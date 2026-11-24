package com.uev.aspect;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 缓存注解 —— 打在 Service 方法上，由 {@link CacheAspect} 统一拦截。
 *
 * <p>TTL 按契约 03 · 1.4：
 * KPI 300s、分区占用率 600s、图表 120s。
 *
 * @author 杨珊珊（D 岗）
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface UevCache {

    /** key 前缀，例如 uev:chart:hourly */
    String prefix();

    /** 过期秒数，<= 0 表示不缓存 */
    int ttl() default 120;
}
