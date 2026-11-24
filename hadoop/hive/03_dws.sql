-- ==============================================================================
-- 03_dws.sql —— DWS 汇总层建表 + 聚合（4 张表）
--
-- 维护人：苏静（B 岗）　|　口径来源：docs/contracts/04-数仓表结构规范.md v1.0
-- 执行方式：spark-sql --master local[*] -f 03_dws.sql
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS uev_dws;
USE uev_dws;

-- ----------------------------------------------------------------------
-- ① 分区 x 日 x 小时 事实表（ADS 层直接消费，9 字段）
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dws.zone_day_hour (
  zone_id        STRING,
  dt             STRING,
  hour_of_day    INT,
  occupancy      DOUBLE,
  duration_h     DOUBLE,
  volume_kwh     DOUBLE,
  e_price        DOUBLE,
  s_price        DOUBLE,
  charge_count   INT
)
COMMENT '分区 x 日 x 小时 事实表（ADS 层直接消费）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ② 分区日汇总（11 字段）
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dws.zone_day (
  zone_id         STRING,
  dt              STRING,
  avg_occupancy   DOUBLE COMMENT '日均占用率',
  max_occupancy   DOUBLE,
  avg_duration    DOUBLE,
  total_volume    DOUBLE,
  avg_e_price     DOUBLE,
  peak_hour       INT    COMMENT '峰值小时',
  valley_hour     INT    COMMENT '谷值小时',
  peak_valley_gap DOUBLE COMMENT '峰谷差',
  occupancy_std   DOUBLE COMMENT '日内波动率'
)
COMMENT '分区日粒度汇总'
PARTITIONED BY (dt STRING)
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ③ 分区 x 小时 画像（跨天平均，峰谷分析用）
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dws.zone_hour_profile (
  zone_id        STRING,
  hour_of_day    INT,
  avg_occupancy  DOUBLE,
  avg_duration   DOUBLE,
  avg_volume     DOUBLE,
  sample_days    INT
)
COMMENT '分区 x 小时 画像表（峰谷分析用）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ④ 分区聚类特征宽表（创新点④，7 维特征）
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dws.zone_cluster_features (
  zone_id           STRING  COMMENT '交通分区编号',
  avg_occupancy     DOUBLE  COMMENT '特征1 平均占用率 0-1',
  peak_valley_gap   DOUBLE  COMMENT '特征2 日内峰谷差',
  occupancy_std     DOUBLE  COMMENT '特征3 占用率标准差（波动率）',
  avg_duration      DOUBLE  COMMENT '特征4 平均充电时长（小时）',
  poi_density       DOUBLE  COMMENT '特征5 POI 密度（个/km²）',
  pile_density      DOUBLE  COMMENT '特征6 充电桩密度（个/km²）',
  price_std         DOUBLE  COMMENT '特征7 电价时序标准差（分时电价识别）'
)
COMMENT '分区聚类特征宽表（7 维特征，每行一分区）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ==============================================================================
-- 聚合：DWD 长表 → DWS 汇总
-- ==============================================================================

-- ① 分区 x 日 x 小时 事实表（宽表 pivot 回长表，6 指标按 MAX 合并）
INSERT OVERWRITE TABLE uev_dws.zone_day_hour
SELECT
    m.zone_id,
    m.dt,
    m.hour_of_day,
    MAX(CASE WHEN m.metric = 'occupancy' THEN m.value END) AS occupancy,
    MAX(CASE WHEN m.metric = 'duration'  THEN m.value END) AS duration_h,
    MAX(CASE WHEN m.metric = 'volume'    THEN m.value END) AS volume_kwh,
    MAX(CASE WHEN m.metric = 'e_price'   THEN m.value END) AS e_price,
    MAX(CASE WHEN m.metric = 's_price'   THEN m.value END) AS s_price,
    di.charge_count
FROM uev_dwd.zone_hour_metric m
LEFT JOIN uev_dwd.dim_zone_info di ON m.zone_id = di.zone_id
GROUP BY m.zone_id, m.dt, m.hour_of_day, di.charge_count;

-- ② 分区日汇总
INSERT OVERWRITE TABLE uev_dws.zone_day PARTITION (dt)
SELECT
    zone_id,
    AVG(occupancy)   AS avg_occupancy,
    MAX(occupancy)   AS max_occupancy,
    AVG(duration_h)  AS avg_duration,
    SUM(volume_kwh)  AS total_volume,
    AVG(e_price)     AS avg_e_price,
    CAST(FIRST(hour_of_day, 1) AS INT) AS peak_hour,
    CAST(LAST(hour_of_day, 1)  AS INT) AS valley_hour,
    MAX(occupancy) - MIN(occupancy)   AS peak_valley_gap,
    STDDEV_POP(occupancy)             AS occupancy_std,
    dt
FROM uev_dws.zone_day_hour
GROUP BY zone_id, dt;

-- ③ 分区 x 小时 画像（跨天平均）
INSERT OVERWRITE TABLE uev_dws.zone_hour_profile
SELECT
    zone_id,
    hour_of_day,
    AVG(occupancy)  AS avg_occupancy,
    AVG(duration_h) AS avg_duration,
    AVG(volume_kwh) AS avg_volume,
    COUNT(DISTINCT dt) AS sample_days
FROM uev_dws.zone_day_hour
GROUP BY zone_id, hour_of_day;

-- ④ 聚类特征宽表（POI 密度 / 桩密度按 km² 换算，area 单位 m² → ×1e6）
INSERT OVERWRITE TABLE uev_dws.zone_cluster_features
SELECT
    d.zone_id,
    d.avg_occupancy,
    d.peak_valley_gap,
    d.occupancy_std,
    d.avg_duration,
    di.poi_total / di.area * 1000000.0        AS poi_density,
    di.charge_count / di.area * 1000000.0     AS pile_density,
    di.price_std
FROM uev_dws.zone_day d
JOIN uev_dwd.dim_zone_info di ON d.zone_id = di.zone_id
GROUP BY d.zone_id, d.avg_occupancy, d.peak_valley_gap, d.occupancy_std,
         d.avg_duration, di.poi_total, di.area, di.charge_count, di.price_std;

-- ----------------------------------------------------------------------
-- 校验
-- ----------------------------------------------------------------------
-- SELECT COUNT(*) FROM uev_dws.zone_day_hour;      -- 期望 275 × 181 × 24
-- SELECT COUNT(*) FROM uev_dws.zone_cluster_features; -- 期望 275
-- ==============================================================================
