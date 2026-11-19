package com.uev;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 城市充电桩使用行为分析与充电需求预测系统 —— 后端启动类
 *
 * <p>维护人：D（杨珊珊）
 * <p>骨架由 A（彭忠燕）提供，2026-11-19
 *
 * @author uev-team
 */
@SpringBootApplication
@EnableCaching      // Redis 缓存
@EnableScheduling   // 定时刷新缓存（可选）
public class UevChargeAnalysisApplication {

    public static void main(String[] args) {
        SpringApplication.run(UevChargeAnalysisApplication.class, args);
        System.out.println("""

                ============================================================
                  UEV 充电桩分析系统 · 后端启动成功
                  接口地址: http://localhost:8080/api
                  健康检查: http://localhost:8080/api/health
                ============================================================
                """);
    }
}
