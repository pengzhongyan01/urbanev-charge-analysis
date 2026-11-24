package com.uev.entity;

import lombok.Data;

/**
 * price_elasticity 表实体 —— 创新点② 分时电价弹性。
 *
 * <p>priceType：TOU = 分时电价区，FLAT = 固定电价区（由 E02 的 σ_price 反推）。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class PriceElasticity {
    private Long id;
    private String priceType;
    private Integer hourOfDay;
    private Double avgOccupancy;
    private Integer zoneCount;
    private Double avgPriceGap;
}
