package com.uev.controller;

import com.uev.common.Result;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;
import java.sql.Connection;
import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 健康检查接口
 *
 * <p>维护人：A（彭忠燕）—— 启停脚本与冒烟测试依赖此接口
 *
 * <p>用途：
 * <ul>
 *   <li>{@code scripts/start_all.sh} 判断后端是否就绪</li>
 *   <li>{@code scripts/smoke_test.sh} 端到端体检</li>
 *   <li>答辩现场一键确认系统状态</li>
 * </ul>
 *
 * <p>返回各依赖组件的连通状态，一眼看出哪里挂了。
 */
@Slf4j
@RestController
@RequestMapping("/api")
public class HealthController {

    private final DataSource dataSource;
    private final RedisTemplate<String, Object> redisTemplate;
    private final JdbcTemplate jdbcTemplate;

    @Value("${uev.data.region-count:275}")
    private int regionCount;

    public HealthController(DataSource dataSource,
                            RedisTemplate<String, Object> redisTemplate,
                            JdbcTemplate jdbcTemplate) {
        this.dataSource = dataSource;
        this.redisTemplate = redisTemplate;
        this.jdbcTemplate = jdbcTemplate;
    }

    /**
     * 健康检查（存活探针）
     *
     * @return 各组件状态
     */
    @GetMapping("/health")
    public Result<Map<String, Object>> health() {
        Map<String, Object> info = new LinkedHashMap<>();
        info.put("status", "UP");
        info.put("timestamp", LocalDateTime.now().toString());
        info.put("application", "uev-charge-analysis");
        info.put("version", "1.0.0");
        info.put("regionCount", regionCount);

        Map<String, Object> components = new LinkedHashMap<>();
        components.put("mysql", checkMysql());
        components.put("redis", checkRedis());
        info.put("components", components);

        boolean allOk = "UP".equals(components.get("mysql"))
                && "UP".equals(components.get("redis"));
        if (!allOk) {
            info.put("status", "DEGRADED");
        }

        return Result.success(info);
    }

    /** 检查 MySQL 连通性 */
    private String checkMysql() {
        try (Connection conn = dataSource.getConnection()) {
            Integer cnt = jdbcTemplate.queryForObject("SELECT 1", Integer.class);
            return (cnt != null && cnt == 1) ? "UP" : "DOWN";
        } catch (Exception e) {
            log.warn("MySQL 健康检查失败: {}", e.getMessage());
            return "DOWN";
        }
    }

    /** 检查 Redis 连通性 */
    private String checkRedis() {
        try {
            String pong = (String) redisTemplate.getConnectionFactory()
                    .getConnection().ping();
            return "PONG".equalsIgnoreCase(pong) ? "UP" : "DOWN";
        } catch (Exception e) {
            log.warn("Redis 健康检查失败: {}", e.getMessage());
            return "DOWN";
        }
    }
}
