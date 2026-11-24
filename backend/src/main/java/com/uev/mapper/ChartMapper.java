package com.uev.mapper;

import com.uev.entity.DemandForecast;
import com.uev.entity.ExpansionSuggestion;
import com.uev.entity.HourlySupplyDemand;
import com.uev.entity.ImbalanceIndex;
import com.uev.entity.PoiCorrelation;
import com.uev.entity.PriceElasticity;
import com.uev.entity.VolumeDeviation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 图表读接口 —— 全部落在 ADS 层视图上，Service 只做组装，不写聚合 SQL。
 *
 * @author 杨姗姗（D 岗）
 */
@Mapper
public interface ChartMapper {

    /** 24 小时供需曲线 */
    List<HourlySupplyDemand> selectHourly(@Param("hourFrom") Integer hourFrom,
                                          @Param("hourTo") Integer hourTo);

    /** 供需失衡 TOP N（创新点①） */
    List<ImbalanceIndex> selectImbalanceTop(@Param("zoneId") String zoneId,
                                            @Param("hourFrom") Integer hourFrom,
                                            @Param("hourTo") Integer hourTo,
                                            @Param("limit") Integer limit);

    /** 电价弹性：按 TOU / FLAT 分组取一整天的 24 个点 */
    List<PriceElasticity> selectPriceByType(@Param("priceType") String priceType);

    /** 需求预测（创新点③） */
    List<DemandForecast> selectForecast(@Param("zoneId") String zoneId,
                                        @Param("startDate") String startDate,
                                        @Param("endDate") String endDate,
                                        @Param("limit") Integer limit);

    /** 布点扩容建议（创新点③） */
    List<ExpansionSuggestion> selectSuggestions(@Param("limit") Integer limit);

    /** 双口径电量偏差（可选接口） */
    List<VolumeDeviation> selectVolumeDeviation(@Param("zoneId") String zoneId);

    /** POI 关联分析（可选接口） */
    List<PoiCorrelation> selectPoiCorrelation(@Param("zoneId") String zoneId);
}
