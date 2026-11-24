package com.uev.entity;

import lombok.Data;

/**
 * demand_forecast 表实体 —— 创新点③ 需求预测。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class DemandForecast {
    private Long id;
    private String zoneId;
    private String forecastDate;
    private Integer hourOfDay;
    private Double predictVolume;
    private Double actualVolume;
    private Double mape;
}
