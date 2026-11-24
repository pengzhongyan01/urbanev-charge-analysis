package com.uev.vo;

import lombok.Data;

/**
 * 电价弹性双曲线上的一个点 —— 契约 03 · 2.6。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class PricePointVO {
    private Integer hourOfDay;
    private Double avgOccupancy;
    private Integer zoneCount;
    private Double avgPriceGap;
}
