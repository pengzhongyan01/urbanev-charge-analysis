package com.uev.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

/**
 * zone_occupancy 表实体 —— 对应 /api/zones/occupancy（热力图 / 地图）。
 *
 * <p>注意：{@code avgOccupancy} 是 0-1 的比例，不是百分数（契约 03 明示）。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class ZoneOccupancy {
    @JsonIgnore
    private Long id;
    private String zoneId;
    private Double longitude;
    private Double latitude;
    private Double avgOccupancy;
    private Double maxOccupancy;
    private Integer chargeCount;
    private Integer poiTotal;
}
