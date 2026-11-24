package com.uev.controller;

import com.uev.common.ApiResponse;
import com.uev.service.SystemService;
import com.uev.vo.CacheStatsVO;
import com.uev.vo.HealthVO;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 系统接口：健康检查（契约 03 · 2.1）+ 缓存统计（D07 取数用）。
 *
 * <p>Controller 层只做三件事：接参数、调 Service、包 ApiResponse。
 * 不写 if-else 判空、不写 try-catch、不写 SQL —— 这是 D01 分层规范的红线。
 *
 * @author 杨姗姗（D 岗）
 */
@RestController
@RequestMapping("/api")
@RequiredArgsConstructor
public class SystemController {

    private final SystemService systemService;

    /** 2.1 健康检查 */
    @GetMapping("/health")
    public ApiResponse<HealthVO> health() {
        return ApiResponse.ok(systemService.health());
    }

    /** 缓存统计：命中率、命中/未命中平均耗时、加速比 */
    @GetMapping("/system/cache-stats")
    public ApiResponse<CacheStatsVO> cacheStats() {
        return ApiResponse.ok(systemService.cacheStats());
    }

    /** 重置统计：做性能对比前先清一次，保证两次采样互不干扰 */
    @PostMapping("/system/cache-stats/reset")
    public ApiResponse<Void> resetCacheStats() {
        systemService.resetCacheStats();
        return ApiResponse.ok();
    }
}
