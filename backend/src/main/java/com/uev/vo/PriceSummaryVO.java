package com.uev.vo;

import lombok.Data;

/**
 * /api/charts/price-elasticity 的 summary —— 直接给 PPT 用的一句话结论。
 *
 * <pre>
 * summary.touElasticity  = TOU 组峰谷差（越小说明分时电价削峰越有效）
 * summary.flatElasticity = FLAT 组峰谷差
 * </pre>
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class PriceSummaryVO {
    private Double touElasticity;
    private Double flatElasticity;
    private Double touGap;
    private Double flatGap;
    private Integer touZoneCount;
    private Integer flatZoneCount;
}
