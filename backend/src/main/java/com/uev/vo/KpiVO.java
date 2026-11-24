package com.uev.vo;

import lombok.Data;

import java.util.List;

/**
 * /api/dashboard/kpi 的 data 载荷 —— 首页 5 个指标卡 + 分区下拉框。
 *
 * <p>字段名与契约 03 · 2.2 完全一致（大小写敏感，前端按名字取值）。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class KpiVO {
    private Integer stationCount;
    private Integer pileCount;
    /** 0-1 比例，前端自己 ×100 */
    private Double avgOccupancy;
    private Double totalVolume;
    private Double avgDuration;
    private Integer imbalanceZones;
    private List<RegionVO> regions;
}
