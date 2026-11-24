package com.uev.controller;

import com.uev.common.ApiResponse;
import com.uev.common.QueryParams;
import com.uev.service.KpiService;
import com.uev.vo.KpiVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 首页 KPI 接口（契约 03 · 2.2）。
 *
 * @author 杨珊珊（D 岗）
 */
@Validated
@RestController
@RequestMapping("/api/dashboard")
@RequiredArgsConstructor
public class DashboardController {

    private final KpiService kpiService;

    @GetMapping("/kpi")
    public ApiResponse<KpiVO> kpi(@Valid QueryParams params) {
        return ApiResponse.ok(kpiService.getKpi(params));
    }
}
