package com.uev.vo;

import lombok.Data;

import java.util.List;

/**
 * /api/charts/forecast 的 data 载荷：{ "mape": 11.32, "series": [ ... ] }。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class ForecastVO {
    /** 全局平均绝对百分比误差（%），由各行 mape 取平均得到 */
    private Double mape;
    private List<ForecastPointVO> series;
}
