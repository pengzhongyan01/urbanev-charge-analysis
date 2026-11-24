package com.uev.service;

import com.uev.config.CacheService;
import com.uev.vo.CacheStatsVO;
import com.uev.vo.HealthVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 系统服务：健康检查 + 缓存统计。
 *
 * <p>健康检查故意做成"永远返回 200"，把组件状态放在 body 里：
 * 前端状态灯需要读 components，如果 MySQL 挂了直接返回 HTTP 500，
 * 前端只会显示"后端未连接"，反而看不出是哪个组件出了问题。
 *
 * @author 杨姗姗（D 岗）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SystemService {

    private final DataSource dataSource;
    private final CacheService cacheService;

    @Value("${uev.data.region-count:275}")
    private int regionCount;

    @Value("${spring.application.name:uev-charge-analysis}")
    private String appName;

    @Value("${uev.version:1.0.0}")
    private String version;

    public HealthVO health() {
        HealthVO vo = new HealthVO();
        Map<String, String> components = new LinkedHashMap<>();
        boolean mysqlUp = checkMysql();
        components.put("mysql", mysqlUp ? "UP" : "DOWN");
        components.put("redis", cacheService.type().equals("redis") ? "UP" : "DOWN");

        vo.setComponents(components);
        vo.setStatus(mysqlUp ? (components.get("redis").equals("UP") ? "UP" : "DEGRADED") : "DEGRADED");
        vo.setTimestamp(LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss")));
        vo.setApplication(appName);
        vo.setVersion(version);
        vo.setRegionCount(regionCount);
        return vo;
    }

    public CacheStatsVO cacheStats() {
        return cacheService.stats();
    }

    public void resetCacheStats() {
        cacheService.resetStats();
    }

    /** 真连一次库，失败只记 warn，绝不向上抛（健康检查本身不能因为依赖挂掉而 500） */
    private boolean checkMysql() {
        try (Connection conn = dataSource.getConnection();
             Statement st = conn.createStatement();
             ResultSet rs = st.executeQuery("SELECT 1")) {
            return rs.next();
        } catch (Exception e) {
            log.warn("[健康检查] MySQL 不可用：{}", e.getMessage());
            return false;
        }
    }
}
