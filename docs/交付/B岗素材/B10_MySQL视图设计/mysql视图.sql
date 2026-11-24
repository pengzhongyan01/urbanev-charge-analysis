-- ==============================================================================
-- mysql视图.sql —— MySQL 视图设计（4 张，B 建 / D 只读）
--
-- 维护人：苏静（B 岗）　|　口径来源：docs/report/第3-4章_初稿.md 4.4.4
-- 设计意图：ads_*（B 离线管道）与 insight_*（E 探索性分析）在视图层汇合
-- ==============================================================================

USE uev_charge;

-- ----------------------------------------------------------------------
-- ① v_zone_daily：分区日汇总（属性补全）
--    消费接口：GET /api/zones/occupancy、GET /api/dashboard/kpi
-- ----------------------------------------------------------------------
CREATE OR REPLACE VIEW v_zone_daily AS
SELECT
    zo.zone_id,
    zo.longitude,
    zo.latitude,
    zo.avg_occupancy,
    zo.max_occupancy,
    zo.charge_count,
    zo.poi_total,
    kpi.avg_occupancy AS city_avg_occupancy,
    kpi.total_volume  AS city_total_volume,
    kpi.avg_duration  AS city_avg_duration
FROM ads_zone_occupancy zo
CROSS JOIN ads_dashboard_kpi kpi;

-- ----------------------------------------------------------------------
-- ② v_zone_imbalance：分区失衡指数（双路径并列，一致性互证）
--    消费接口：GET /api/charts/imbalance
-- ----------------------------------------------------------------------
CREATE OR REPLACE VIEW v_zone_imbalance AS
SELECT
    ai.zone_id,
    ai.longitude,
    ai.latitude,
    ai.hour_of_day,
    ai.demand_share  AS demand_share_hive,
    ai.supply_share  AS supply_share_hive,
    ai.imbalance     AS imbalance_hive,
    ai.rank_no,
    ii.imbalance     AS imbalance_insight
FROM ads_imbalance_index ai
LEFT JOIN insight_imbalance ii
       ON ai.zone_id = ii.zone_id AND ai.hour_of_day = ii.hour_of_day;

-- ----------------------------------------------------------------------
-- ③ v_forecast：预测结果与误差评估（精度透明）
--    消费接口：GET /api/charts/forecast
-- ----------------------------------------------------------------------
CREATE OR REPLACE VIEW v_forecast AS
SELECT
    df.zone_id,
    df.forecast_date,
    df.hour_of_day,
    df.predict_volume,
    df.actual_volume,
    df.mape,
    fe.mape  AS overall_mape,
    fe.mae   AS overall_mae,
    fe.rmse  AS overall_rmse
FROM ads_demand_forecast df
LEFT JOIN insight_forecast_error fe ON 1 = 1;

-- ----------------------------------------------------------------------
-- ④ v_advice：布点建议（决策闭环，失衡指数佐证）
--    消费接口：GET /api/charts/suggestions
-- ----------------------------------------------------------------------
CREATE OR REPLACE VIEW v_advice AS
SELECT
    es.zone_id,
    es.longitude,
    es.latitude,
    es.current_piles,
    es.suggested_piles,
    es.priority,
    es.reason,
    es.avg_occupancy,
    es.peak_gap,
    ii.imbalance AS imbalance_insight
FROM ads_expansion_suggestion es
LEFT JOIN insight_imbalance ii ON es.zone_id = ii.zone_id;
