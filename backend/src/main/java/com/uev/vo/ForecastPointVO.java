package com.uev.vo;

import lombok.Data;

/**
 * 预测曲线上的一个点 —— 契约 03 · 2.7。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class ForecastPointVO {
    private String zoneId;
    private String forecastDate;
    private Integer hourOfDay;
    private Double predictVolume;
    private Double actualVolume;
}
