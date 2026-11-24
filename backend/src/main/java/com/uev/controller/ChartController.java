package com.uev.controller;

import com.uev.common.ApiResponse;
import com.uev.common.QueryParams;
import com.uev.entity.ExpansionSuggestion;
import com.uev.service.ChartService;
import com.uev.vo.ForecastVO;
import com.uev.vo.HourlySeriesVO;
import com.uev.vo.ImbalanceTopVO;
import com.uev.vo.PoiCorrelationVO;
import com.uev.vo.PriceElasticityVO;
import com.uev.vo.VolumeDeviationVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 图表接口 —— 6 个图表（契约 03 · 2.4 ~ 2.10）。
 *
 * @author 杨姗姗（D 岗）
 */
@Validated
@RestController
@RequestMapping("/api/charts")
@RequiredArgsConstructor
public class ChartController {

    private final ChartService chartService;

    /** 2.4 24 小时供需曲线 */
    @GetMapping("/hourly")
    public ApiResponse<HourlySeriesVO> hourly(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getHourly(params));
    }

    /** 2.5 供需失衡 TOP（★ 创新点①） */
    @GetMapping("/imbalance")
    public ApiResponse<ImbalanceTopVO> imbalance(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getImbalance(params));
    }

    /** 2.6 电价弹性双曲线（★ 创新点②） */
    @GetMapping("/price-elasticity")
    public ApiResponse<PriceElasticityVO> priceElasticity(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getPriceElasticity(params));
    }

    /** 2.7 需求预测曲线（★ 创新点③） */
    @GetMapping("/forecast")
    public ApiResponse<ForecastVO> forecast(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getForecast(params));
    }

    /** 2.8 布点扩容建议（★ 创新点③） */
    @GetMapping("/suggestions")
    public ApiResponse<List<ExpansionSuggestion>> suggestions(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getSuggestions(params));
    }

    /** 2.9 双口径电量偏差（可选） */
    @GetMapping("/volume-deviation")
    public ApiResponse<VolumeDeviationVO> volumeDeviation(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getVolumeDeviation(params));
    }

    /** 2.10 POI 关联分析（可选） */
    @GetMapping("/poi-correlation")
    public ApiResponse<PoiCorrelationVO> poiCorrelation(@Valid QueryParams params) {
        return ApiResponse.ok(chartService.getPoiCorrelation(params));
    }
}
