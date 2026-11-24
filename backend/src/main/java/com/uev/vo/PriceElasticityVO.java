package com.uev.vo;

import lombok.Data;

import java.util.List;

/**
 * /api/charts/price-elasticity 的 data 载荷：TOU / FLAT 两组曲线 + summary。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class PriceElasticityVO {
    private List<PricePointVO> tou;
    private List<PricePointVO> flat;
    private PriceSummaryVO summary;
}
