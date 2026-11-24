package com.uev.config;

import com.uev.aspect.CacheContext;
import com.uev.entity.QueryLog;
import com.uev.mapper.SystemMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 查询日志拦截器 —— 把每个接口的耗时、参数、是否命中缓存写进 query_log 表。
 *
 * <p>答辩价值：老师说"你怎么证明缓存真的生效了"，直接打开 query_log 表，
 * 同一条接口连续两次请求 hit_cache 从 0 变 1、cost_ms 从几十毫秒掉到几毫秒。
 *
 * <p>性能保护：健康检查与缓存统计接口不落库，避免监控请求把日志表刷爆；
 * 落库失败只打 WARN，绝不影响业务响应。
 *
 * @author 杨姗姗（D 岗）
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class QueryLogInterceptor implements HandlerInterceptor {

    private static final String ATTR_START = "uev.startNanos";
    private static final int MAX_PARAMS_LEN = 500;

    private final SystemMapper systemMapper;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute(ATTR_START, System.nanoTime());
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response,
                                Object handler, Exception ex) {
        Object start = request.getAttribute(ATTR_START);
        String uri = request.getRequestURI();
        try {
            if (start instanceof Long && shouldLog(uri)) {
                long costMs = (System.nanoTime() - (Long) start) / 1_000_000;
                QueryLog logRow = new QueryLog();
                logRow.setApiPath(uri);
                String qs = request.getQueryString();
                logRow.setParams(qs == null ? "" :
                        (qs.length() > MAX_PARAMS_LEN ? qs.substring(0, MAX_PARAMS_LEN) : qs));
                logRow.setCostMs((int) costMs);
                logRow.setHitCache(CacheContext.isHit() ? 1 : 0);
                systemMapper.insertQueryLog(logRow);
            }
        } catch (Exception e) {
            log.warn("[查询日志] 落库失败（不影响业务）：{}", e.getMessage());
        } finally {
            CacheContext.clear();
        }
    }

    private boolean shouldLog(String uri) {
        return !(uri.startsWith("/api/health") || uri.startsWith("/api/system"));
    }
}
