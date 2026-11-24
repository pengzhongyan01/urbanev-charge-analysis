-- ==============================================================================
-- 04_ads.sql —— ADS 应用层建表（8 张表，一张表 = 前端一张图）
--
-- 维护人：苏静（B 岗）　|　口径来源：docs/contracts/04-数仓表结构规范.md v1.0
-- 计算逻辑见 hadoop/spark/ads_metrics.sql（B07），本文件只负责建表
-- 落地后由 Sqoop export 到 MySQL（B09）
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS uev_ads;
USE uev_ads;

-- ① KPI 概览（首页 5 个指标卡）
CREATE TABLE IF NOT EXISTS uev_ads.dashboard_kpi (
  dt               STRING,
  station_count    INT,
  pile_count       INT,
  avg_occupancy    DOUBLE,
  total_volume     DOUBLE,
  avg_duration     DOUBLE,
  imbalance_zones  INT,
  compute_time     TIMESTAMP
) STORED AS ORC;

-- ② 分区占用率（前端热力图 / 地图）
CREATE TABLE IF NOT EXISTS uev_ads.zone_occupancy (
  zone_id       STRING,
  longitude     DOUBLE,
  latitude      DOUBLE,
  avg_occupancy DOUBLE,
  max_occupancy DOUBLE,
  charge_count  INT,
  poi_total     INT
) STORED AS ORC;

-- ③ 24 小时供需曲线（前端折线图）
CREATE TABLE IF NOT EXISTS uev_ads.hourly_supply_demand (
  hour_of_day   INT,
  avg_occupancy DOUBLE,
  avg_demand    DOUBLE,
  avg_supply    DOUBLE,
  gap           DOUBLE,
  imbalance     DOUBLE
) STORED AS ORC;

-- ④ 供需失衡指数 TOP N（前端柱状图）★ 创新点①
CREATE TABLE IF NOT EXISTS uev_ads.imbalance_index (
  zone_id      STRING,
  longitude    DOUBLE,
  latitude     DOUBLE,
  dt           STRING,
  hour_of_day  INT,
  demand       DOUBLE,
  supply       DOUBLE,
  imbalance    DOUBLE,
  rank_no      INT
) STORED AS ORC;

-- ⑤ 电价弹性对比（前端双曲线图）★ 创新点②
CREATE TABLE IF NOT EXISTS uev_ads.price_elasticity (
  price_type     STRING,
  hour_of_day    INT,
  avg_occupancy  DOUBLE,
  zone_count     INT,
  avg_price_gap  DOUBLE
) STORED AS ORC;

-- ⑥ 需求预测结果（前端预测曲线）★ 创新点③
CREATE TABLE IF NOT EXISTS uev_ads.demand_forecast (
  zone_id        STRING,
  forecast_date  STRING,
  hour_of_day    INT,
  predict_volume DOUBLE,
  actual_volume  DOUBLE,
  mape           DOUBLE
) STORED AS ORC;

-- ⑦ 布点扩容建议（前端建议看板）★ 创新点③
CREATE TABLE IF NOT EXISTS uev_ads.expansion_suggestion (
  zone_id         STRING,
  longitude       DOUBLE,
  latitude        DOUBLE,
  current_piles   INT,
  suggested_piles INT,
  priority        INT,
  reason          STRING,
  avg_occupancy   DOUBLE,
  peak_gap        DOUBLE
) STORED AS ORC;

-- ⑧ 分区聚类结果（创新点④，由 zone_clustering.sql + ZoneClustering.scala 产出）
CREATE TABLE IF NOT EXISTS uev_ads.zone_cluster (
  zone_id         STRING,
  cluster_id      INT,
  cluster_name    STRING,
  avg_occupancy   DOUBLE,
  peak_valley_gap DOUBLE,
  occupancy_std   DOUBLE,
  avg_duration    DOUBLE,
  poi_density     DOUBLE,
  pile_density    DOUBLE,
  price_std       DOUBLE,
  longitude       DOUBLE,
  latitude        DOUBLE
) STORED AS ORC;

-- ----------------------------------------------------------------------
-- 实测产出规模（A 岗 Python 路径实跑，B 岗 Hive 侧需逐项一致）
-- dashboard_kpi          1 行
-- zone_occupancy       275 行
-- hourly_supply_demand  24 行
-- imbalance_index      200 行（TOP 200）
-- price_elasticity      24 行
-- demand_forecast     3850 行（275 分区 × 14 天回测）
-- expansion_suggestion 167 行
-- zone_cluster         275 行
-- ==============================================================================
