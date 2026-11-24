package com.uev.entity;

import lombok.Data;

/**
 * dashboard_kpi 表实体（ADS 层导出表）—— 对应契约 03 的 /api/dashboard/kpi。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class DashboardKpi {
    private Long id;
    /** 统计日期，全量统计为 ALL */
    private String dt;
    private Integer stationCount;
    private Integer pileCount;
    private Double avgOccupancy;
    private Double totalVolume;
    private Double avgDuration;
    private Integer imbalanceZones;
    private String computeTime;
}
