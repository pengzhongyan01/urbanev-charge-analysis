package com.uev.vo;

import lombok.Data;

/**
 * 24 小时曲线的一个点 —— 契约 03 · 2.4。
 *
 * <p>数据库列名是 avg_demand / avg_supply，接口字段是 demandShare / supplyShare，
 * 名字必须对齐接口规范，这个转换放在 Service 层完成（不要在前端硬改）。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class HourlyVO {
    private Integer hourOfDay;
    private Double avgOccupancy;
    private Double demandShare;
    private Double supplyShare;
    private Double gap;
    private Double imbalance;
}
