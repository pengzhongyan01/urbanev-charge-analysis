package com.uev.vo;

import com.uev.entity.PoiCorrelation;
import lombok.Data;

import java.util.List;

/**
 * /api/charts/poi-correlation 的 data 载荷（契约 03 · 2.10）。
 *
 * <p>correlation 里的皮尔逊系数由 Service 层对 rows 现算（MySQL 没有 CORREL 函数），
 * 这样即使 B 岗还没灌 poi_correlation 表，接口也不会报 500，只会返回空列表。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class PoiCorrelationVO {

    private List<PoiCorrelation> zones;
    private Correlation summary;

    @Data
    public static class Correlation {
        /** POI 密度与占用率的皮尔逊相关系数 */
        private Double poiDensityVsOccupancy;
    }

    public static PoiCorrelationVO of(List<PoiCorrelation> zones, Double corr) {
        PoiCorrelationVO vo = new PoiCorrelationVO();
        vo.setZones(zones);
        Correlation c = new Correlation();
        c.setPoiDensityVsOccupancy(corr);
        vo.setSummary(c);
        return vo;
    }
}
