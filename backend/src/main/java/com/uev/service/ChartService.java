package com.uev.service;

import com.uev.aspect.UevCache;
import com.uev.common.QueryParams;
import com.uev.entity.DemandForecast;
import com.uev.entity.ExpansionSuggestion;
import com.uev.entity.HourlySupplyDemand;
import com.uev.entity.ImbalanceIndex;
import com.uev.entity.PoiCorrelation;
import com.uev.entity.PriceElasticity;
import com.uev.entity.VolumeDeviation;
import com.uev.mapper.ChartMapper;
import com.uev.vo.ForecastPointVO;
import com.uev.vo.ForecastVO;
import com.uev.vo.HourlySeriesVO;
import com.uev.vo.HourlyVO;
import com.uev.vo.ImbalanceTopVO;
import com.uev.vo.PoiCorrelationVO;
import com.uev.vo.PriceElasticityVO;
import com.uev.vo.PricePointVO;
import com.uev.vo.PriceSummaryVO;
import com.uev.vo.VolumeDeviationVO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

/**
 * 图表服务 —— 7 个图表接口的组装逻辑。
 *
 * <p>分层原则：SQL 只做"取数"，字段改名、补 summary、算相关系数这类事
 * 全部放在这一层，Controller 只负责包 {@code ApiResponse}。
 *
 * <p>缓存 120 秒（契约 1.4 的图表 TTL）。
 *
 * @author 杨姗姗（D 岗）
 */
@Service
@RequiredArgsConstructor
public class ChartService {

    private static final int DEFAULT_IMBALANCE_LIMIT = 10;
    private static final int DEFAULT_SUGGESTION_LIMIT = 30;
    private static final int DEFAULT_FORECAST_LIMIT = 500;

    private final ChartMapper chartMapper;

    /** 契约 03 · 2.4 24 小时供需曲线 */
    @UevCache(prefix = "uev:chart:hourly", ttl = 120)
    public HourlySeriesVO getHourly(QueryParams params) {
        params.validate();
        List<HourlySupplyDemand> rows = chartMapper.selectHourly(params.hourFrom(), params.hourTo());
        List<HourlyVO> points = new ArrayList<>(rows.size());
        for (HourlySupplyDemand row : rows) {
            HourlyVO vo = new HourlyVO();
            vo.setHourOfDay(row.getHourOfDay());
            vo.setAvgOccupancy(row.getAvgOccupancy());
            // 列名 avg_demand / avg_supply → 接口字段 demandShare / supplyShare
            vo.setDemandShare(row.getAvgDemand());
            vo.setSupplyShare(row.getAvgSupply());
            vo.setGap(row.getGap());
            vo.setImbalance(row.getImbalance());
            points.add(vo);
        }
        HourlySeriesVO series = new HourlySeriesVO();
        series.setHourly(points);
        return series;
    }

    /** 契约 03 · 2.5 供需失衡 TOP N（创新点①） */
    @UevCache(prefix = "uev:chart:imbalance", ttl = 120)
    public ImbalanceTopVO getImbalance(QueryParams params) {
        params.validate();
        int limit = params.getLimit() == null ? DEFAULT_IMBALANCE_LIMIT : params.getLimit();
        List<ImbalanceIndex> rows = chartMapper.selectImbalanceTop(
                params.getZoneId(), params.hourFrom(), params.hourTo(), limit);
        ImbalanceTopVO vo = new ImbalanceTopVO();
        vo.setTop(rows);
        return vo;
    }

    /** 契约 03 · 2.6 电价弹性 TOU/FLAT 双曲线（创新点②） */
    @UevCache(prefix = "uev:chart:price", ttl = 120)
    public PriceElasticityVO getPriceElasticity(QueryParams params) {
        params.validate();
        List<PriceElasticity> touRows = chartMapper.selectPriceByType("TOU");
        List<PriceElasticity> flatRows = chartMapper.selectPriceByType("FLAT");

        PriceElasticityVO vo = new PriceElasticityVO();
        vo.setTou(toPricePoints(touRows));
        vo.setFlat(toPricePoints(flatRows));

        PriceSummaryVO summary = new PriceSummaryVO();
        summary.setTouElasticity(peakValleyGap(vo.getTou()));
        summary.setFlatElasticity(peakValleyGap(vo.getFlat()));
        summary.setTouGap(avgPriceGap(touRows));
        summary.setFlatGap(avgPriceGap(flatRows));
        summary.setTouZoneCount(maxZoneCount(touRows));
        summary.setFlatZoneCount(maxZoneCount(flatRows));
        vo.setSummary(summary);
        return vo;
    }

    /** 契约 03 · 2.7 需求预测（创新点③） */
    @UevCache(prefix = "uev:chart:forecast", ttl = 120)
    public ForecastVO getForecast(QueryParams params) {
        params.validate();
        int limit = params.getLimit() == null ? DEFAULT_FORECAST_LIMIT : params.getLimit();
        List<DemandForecast> rows = chartMapper.selectForecast(
                params.getZoneId(),
                params.getStartDate() == null ? null : params.getStartDate().toString(),
                params.getEndDate() == null ? null : params.getEndDate().toString(),
                limit);

        ForecastVO vo = new ForecastVO();
        List<ForecastPointVO> series = new ArrayList<>(rows.size());
        double mapeSum = 0.0;
        int mapeCnt = 0;
        for (DemandForecast row : rows) {
            ForecastPointVO p = new ForecastPointVO();
            p.setZoneId(row.getZoneId());
            p.setForecastDate(row.getForecastDate());
            p.setHourOfDay(row.getHourOfDay());
            p.setPredictVolume(row.getPredictVolume());
            p.setActualVolume(row.getActualVolume());
            series.add(p);
            if (row.getMape() != null) {
                mapeSum += row.getMape();
                mapeCnt++;
            }
        }
        vo.setSeries(series);
        // 全局 MAPE：各行 mape 的算术平均，保留两位（给 PPT 直接念）
        vo.setMape(mapeCnt == 0 ? null : Math.round(mapeSum / mapeCnt * 100.0) / 100.0);
        return vo;
    }

    /** 契约 03 · 2.8 布点扩容建议（创新点③） */
    @UevCache(prefix = "uev:chart:suggestion", ttl = 120)
    public List<ExpansionSuggestion> getSuggestions(QueryParams params) {
        params.validate();
        int limit = params.getLimit() == null ? DEFAULT_SUGGESTION_LIMIT : params.getLimit();
        return chartMapper.selectSuggestions(limit);
    }

    /** 契约 03 · 2.9 双口径电量偏差（可选接口，E 岗灌数） */
    @UevCache(prefix = "uev:chart:volume_dev", ttl = 120)
    public VolumeDeviationVO getVolumeDeviation(QueryParams params) {
        params.validate();
        List<VolumeDeviation> rows = chartMapper.selectVolumeDeviation(params.getZoneId());
        return VolumeDeviationVO.of(rows);
    }

    /** 契约 03 · 2.10 POI 关联分析（可选接口，B 岗灌数） */
    @UevCache(prefix = "uev:chart:poi", ttl = 120)
    public PoiCorrelationVO getPoiCorrelation(QueryParams params) {
        params.validate();
        List<PoiCorrelation> rows = chartMapper.selectPoiCorrelation(params.getZoneId());
        double corr = pearson(
                rows.stream().map(PoiCorrelation::getPoiDensity).toList(),
                rows.stream().map(PoiCorrelation::getAvgOccupancy).toList());
        return PoiCorrelationVO.of(rows, corr);
    }

    // ------------------------------------------------------------------ 工具方法

    private List<PricePointVO> toPricePoints(List<PriceElasticity> rows) {
        List<PricePointVO> points = new ArrayList<>(rows.size());
        for (PriceElasticity row : rows) {
            PricePointVO p = new PricePointVO();
            p.setHourOfDay(row.getHourOfDay());
            p.setAvgOccupancy(row.getAvgOccupancy());
            p.setZoneCount(row.getZoneCount());
            p.setAvgPriceGap(row.getAvgPriceGap());
            points.add(p);
        }
        return points;
    }

    /** 峰谷差：一天内最高占用率 - 最低占用率（越小说明削峰越有效） */
    private Double peakValleyGap(List<PricePointVO> points) {
        if (points == null || points.isEmpty()) {
            return null;
        }
        double max = Double.NEGATIVE_INFINITY;
        double min = Double.POSITIVE_INFINITY;
        for (PricePointVO p : points) {
            if (p.getAvgOccupancy() == null) {
                continue;
            }
            max = Math.max(max, p.getAvgOccupancy());
            min = Math.min(min, p.getAvgOccupancy());
        }
        return max < min ? null : round(max - min);
    }

    private Double avgPriceGap(List<PriceElasticity> rows) {
        if (rows == null || rows.isEmpty()) {
            return null;
        }
        double sum = 0.0;
        int cnt = 0;
        for (PriceElasticity r : rows) {
            if (r.getAvgPriceGap() != null) {
                sum += r.getAvgPriceGap();
                cnt++;
            }
        }
        return cnt == 0 ? null : round(sum / cnt);
    }

    private Integer maxZoneCount(List<PriceElasticity> rows) {
        if (rows == null || rows.isEmpty()) {
            return null;
        }
        int max = 0;
        for (PriceElasticity r : rows) {
            if (r.getZoneCount() != null) {
                max = Math.max(max, r.getZoneCount());
            }
        }
        return max;
    }

    /** 皮尔逊相关系数；样本 < 3 或无方差时返回 null，避免算出 NaN */
    private Double pearson(List<Double> xs, List<Double> ys) {
        if (xs == null || ys == null || xs.size() < 3 || xs.size() != ys.size()) {
            return null;
        }
        int n = xs.size();
        double sx = 0, sy = 0;
        for (int i = 0; i < n; i++) {
            if (xs.get(i) == null || ys.get(i) == null) {
                return null;
            }
            sx += xs.get(i);
            sy += ys.get(i);
        }
        double mx = sx / n, my = sy / n;
        double cov = 0, vx = 0, vy = 0;
        for (int i = 0; i < n; i++) {
            double dx = xs.get(i) - mx;
            double dy = ys.get(i) - my;
            cov += dx * dy;
            vx += dx * dx;
            vy += dy * dy;
        }
        if (vx == 0 || vy == 0) {
            return null;
        }
        return round(cov / Math.sqrt(vx * vy));
    }

    private double round(double v) {
        return Math.round(v * 10000.0) / 10000.0;
    }
}
