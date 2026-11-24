package com.uev.entity;

import lombok.Data;

/**
 * poi_correlation 表实体 —— M9 POI 关联分析（契约 03 · 2.10，可选接口）。
 *
 * <p>由 B 岗（空间维表加工）灌数，D 只负责读。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class PoiCorrelation {
    private Long id;
    private String zoneId;
    private Integer poiTotal;
    private Double poiDensity;
    private Double pileDensity;
    private Double avgOccupancy;
}
