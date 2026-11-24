-- =============================================================================
-- 03_views.sql —— 后端只读视图（D08 接入对象）
-- =============================================================================
-- 维护人：杨姗姗（D 岗）　|　说明：与 01_schema.sql 末尾的视图定义一致，
-- 单独抽出来是方便 B 岗（B10 视图设计）直接替换/评审，也方便答辩时单独讲。
--
-- 【约定】后端 Mapper XML 只 FROM 以下 10 个视图，不直连实体表：
--   v_kpi_overview           ← KpiMapper.selectLatest
--   v_zone_occupancy         ← KpiMapper.selectRegions / ZoneMapper
--   v_zone_hour_profile      ← ZoneMapper.selectZoneHourProfile
--   v_hourly_supply_demand   ← ChartMapper.selectHourly
--   v_imbalance_top          ← ChartMapper.selectImbalanceTop
--   v_price_elasticity       ← ChartMapper.selectPriceByType
--   v_forecast_series        ← ChartMapper.selectForecast
--   v_suggestions            ← ChartMapper.selectSuggestions
--   v_volume_deviation       ← ChartMapper.selectVolumeDeviation
--   v_poi_correlation        ← ChartMapper.selectPoiCorrelation
--
-- 【为什么用视图】
--   1) 口径归口：指标口径变了只改视图/ADS，后端代码不动；
--   2) 权限收口：将来可以只给后端账号视图的 SELECT 权限，表权限收回；
--   3) 字段稳定：视图是"接口字段的数据库投影"，比直接查表更接近契约。
-- =============================================================================

USE uev_charge;

CREATE OR REPLACE VIEW v_kpi_overview AS
SELECT id, dt, station_count, pile_count, avg_occupancy, total_volume,
       avg_duration, imbalance_zones, compute_time
FROM dashboard_kpi;

CREATE OR REPLACE VIEW v_zone_occupancy AS
SELECT zone_id, longitude, latitude, avg_occupancy, max_occupancy, charge_count, poi_total
FROM zone_occupancy;

CREATE OR REPLACE VIEW v_zone_hour_profile AS
SELECT zone_id, hour_of_day, avg_occupancy, avg_duration, avg_volume, sample_days
FROM zone_hour_profile;

CREATE OR REPLACE VIEW v_hourly_supply_demand AS
SELECT hour_of_day, avg_occupancy, avg_demand, avg_supply, gap, imbalance
FROM hourly_supply_demand;

CREATE OR REPLACE VIEW v_imbalance_top AS
SELECT zone_id, longitude, latitude, hour_of_day, demand_share, supply_share, imbalance, rank_no
FROM imbalance_index;

CREATE OR REPLACE VIEW v_price_elasticity AS
SELECT price_type, hour_of_day, avg_occupancy, zone_count, avg_price_gap
FROM price_elasticity;

CREATE OR REPLACE VIEW v_forecast_series AS
SELECT zone_id, forecast_date, hour_of_day, predict_volume, actual_volume, mape
FROM demand_forecast;

CREATE OR REPLACE VIEW v_suggestions AS
SELECT zone_id, longitude, latitude, current_piles, suggested_piles, priority,
       reason, avg_occupancy, peak_gap
FROM expansion_suggestion;

CREATE OR REPLACE VIEW v_volume_deviation AS
SELECT zone_id, volume, volume_11kw, deviation FROM volume_deviation;

CREATE OR REPLACE VIEW v_poi_correlation AS
SELECT zone_id, poi_total, poi_density, pile_density, avg_occupancy FROM poi_correlation;
