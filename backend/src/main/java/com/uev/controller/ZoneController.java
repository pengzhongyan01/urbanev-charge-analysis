package com.uev.controller;

import com.uev.common.ApiResponse;
import com.uev.common.QueryParams;
import com.uev.entity.ZoneOccupancy;
import com.uev.service.ZoneService;
import com.uev.vo.ZoneDetailVO;
import com.uev.vo.ZoneListVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 分区接口：清单 / 占用率热力 / 单分区详情。
 *
 * @author 杨珊珊（D 岗）
 */
@Validated
@RestController
@RequestMapping("/api/zones")
@RequiredArgsConstructor
public class ZoneController {

    private final ZoneService zoneService;

    /** 分区清单（可选关键字搜索） */
    @GetMapping
    public ApiResponse<ZoneListVO> list(
            @RequestParam(required = false) String keyword) {
        return ApiResponse.ok(zoneService.listZones(keyword));
    }

    /** 契约 03 · 2.3 热力图 / 地图散点 */
    @GetMapping("/occupancy")
    public ApiResponse<List<ZoneOccupancy>> occupancy(@Valid QueryParams params) {
        return ApiResponse.ok(zoneService.getOccupancy(params));
    }

    /** 单分区详情 + 峰谷时段 TOP5 */
    @GetMapping("/{zoneId}")
    public ApiResponse<ZoneDetailVO> detail(@PathVariable String zoneId) {
        return ApiResponse.ok(zoneService.getDetail(zoneId));
    }
}
