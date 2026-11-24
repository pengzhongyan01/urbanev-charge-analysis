package com.uev.aspect;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uev.config.CacheService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;

/**
 * 缓存切面 —— 在 Service 方法上做"读缓存 → 回源 → 写缓存"。
 *
 * <p>为什么不在 Controller 上做：Controller 的返回值是泛型 {@code ApiResponse<T>}，
 * 反序列化时拿不到 T 的真实类型；打在 Service 上返回类型是具体的 VO，能精确还原。
 *
 * <p>缓存 key = 前缀 + MD5(方法名 + 全部入参)。入参里有 QueryParams 时，
 * QueryParams.toString() 包含 5 个筛选字段，因此<b>改任何筛选条件都会换 key</b>，
 * 不会出现契约里点名的"改筛选拿到旧数据"的缓存 bug。
 *
 * @author 杨姗姗（D 岗）
 */
@Slf4j
@Aspect
@Component
@RequiredArgsConstructor
public class CacheAspect {

    private final CacheService cacheService;
    private final ObjectMapper objectMapper;

    @Around("@annotation(uevCache)")
    public Object around(ProceedingJoinPoint pjp, UevCache uevCache) throws Throwable {
        String key = buildKey(pjp, uevCache.prefix());
        Class<?> returnType = ((MethodSignature) pjp.getSignature()).getReturnType();

        // 1. 先查缓存
        long t0 = System.nanoTime();
        String cached = cacheService.getRaw(key);
        if (cached != null) {
            long cost = System.nanoTime() - t0;
            cacheService.recordHit(cost);
            CacheContext.setHit(true);
            log.debug("[缓存命中] key={} 耗时={}ms", key, cost / 1_000_000);
            return objectMapper.readValue(cached, returnType);
        }

        // 2. 回源执行
        Object result = pjp.proceed();
        long cost = System.nanoTime() - t0;

        // 3. 回填缓存（结果为空不缓存，避免缓存穿透到空值）
        if (result != null) {
            cacheService.putRaw(key, objectMapper.writeValueAsString(result), uevCache.ttl());
        }
        cacheService.recordMiss(cost);
        CacheContext.setHit(false);
        log.debug("[缓存未命中] key={} 回源耗时={}ms", key, cost / 1_000_000);
        return result;
    }

    private String buildKey(ProceedingJoinPoint pjp, String prefix) {
        StringBuilder sb = new StringBuilder(pjp.getSignature().getName());
        Object[] args = pjp.getArgs();
        if (args != null) {
            for (Object arg : args) {
                sb.append('|').append(arg == null ? "-" : arg.toString());
            }
        }
        return prefix + ":" + md5(sb.toString());
    }

    private String md5(String text) {
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] bytes = md.digest(text.getBytes(StandardCharsets.UTF_8));
            StringBuilder hex = new StringBuilder();
            for (byte b : bytes) {
                hex.append(String.format("%02x", b));
            }
            return hex.toString();
        } catch (Exception e) {
            return Integer.toHexString(text.hashCode());
        }
    }
}
