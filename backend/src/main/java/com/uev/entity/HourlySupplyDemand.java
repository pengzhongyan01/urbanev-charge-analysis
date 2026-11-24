package com.uev.entity;

import lombok.Data;

/**
 * hourly_supply_demand 表实体 —— 24 小时供需曲线。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class HourlySupplyDemand {
    private Long id;
    /** 小时 0-23 */
    private Integer hourOfDay;
    private Double avgOccupancy;
    /** 需求份额 D(t) */
    private Double avgDemand;
    /** 运力份额 S(t) */
    private Double avgSupply;
    private Double gap;
    /** 失衡指数 I(t) */
    private Double imbalance;
}
