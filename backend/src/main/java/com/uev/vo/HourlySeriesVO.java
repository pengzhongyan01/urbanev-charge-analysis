package com.uev.vo;

import lombok.Data;

import java.util.List;

/**
 * /api/charts/hourly 的 data 载荷：{ "hourly": [ ... ] }。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class HourlySeriesVO {
    private List<HourlyVO> hourly;
}
