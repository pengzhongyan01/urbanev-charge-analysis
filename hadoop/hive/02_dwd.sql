-- ==============================================================================
-- 02_dwd.sql —— DWD 明细层建表语句（4 张表）
--
-- 维护人：苏静（B 岗）　|　口径来源：docs/contracts/04-数仓表结构规范.md v1.0
-- 执行顺序：先 01_ods.sql（建 ODS + 宽转长 MR 产出长表），再执行本文件
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS uev_dwd;
USE uev_dwd;

-- ----------------------------------------------------------------------
-- ① 主表：指标标准化长表（由 ODS 宽表经 WideToLong MR explode 而来）
-- 数据量：单指标 275×4344=1,194,600 行，6 指标合计 ≈ 717 万行
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dwd.zone_hour_metric (
  zone_id      STRING COMMENT '交通分区编号',
  hour_ts      STRING COMMENT '小时时间戳 yyyy-MM-dd HH:mm:ss',
  hour_of_day  INT    COMMENT '小时 0-23',
  day_of_week  INT    COMMENT '星期 1-7',
  metric       STRING COMMENT 'occupancy/duration/volume/volume_11kw/e_price/s_price',
  value        DOUBLE COMMENT '指标值（清洗后，异常置 NULL）',
  is_zero      INT    COMMENT '1=原值为0（疑似缺失）0=正常'
)
COMMENT '各指标标准化长表（由 ODS 宽表 explode 而来，已清洗）'
PARTITIONED BY (dt STRING COMMENT '日期分区键 yyyy-MM-dd')
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ② 分区质量画像表（清洗证据，进报告 3.4.3）
-- 由 DataQualityCheck.java 产出
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dwd.dq_zone_stat (
  zone_id      STRING,
  valid_cnt    INT    COMMENT '有效值个数',
  zero_cnt     INT    COMMENT '零值个数（疑似缺失）',
  outlier_cnt  INT    COMMENT '越界值个数',
  total_cnt    INT    COMMENT '总单元格数',
  valid_rate   DOUBLE COMMENT '有效率'
)
COMMENT '分区数据质量画像表'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ③ 分区 POI 计数表（由 PoiZoneJoin.java 产出，712,135 POI 落到 275 分区）
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dwd.zone_poi_count (
  zone_id        STRING COMMENT '分区编号',
  poi_lifestyle  INT    COMMENT '生活服务类 POI 数',
  poi_business   INT    COMMENT '商务居住类 POI 数',
  poi_food       INT    COMMENT '餐饮服务类 POI 数',
  poi_total      INT    COMMENT 'POI 总数'
)
COMMENT '分区 POI 计数表'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ④ 分区综合维度表（E 组创新点②依赖此表）
-- ★ 必须按 TAZID = zone_id 显式 join，禁止按行号对齐（inf.csv 行序≠时序列序）
-- ----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uev_dwd.dim_zone_info (
  zone_id       STRING COMMENT '分区编号（= inf.csv 的 TAZID）',
  longitude     DOUBLE,
  latitude      DOUBLE,
  charge_count  INT    COMMENT '充电桩数',
  area          DOUBLE,
  perimeter     DOUBLE,
  poi_lifestyle INT    COMMENT '生活服务类 POI 数',
  poi_business  INT    COMMENT '商务居住类 POI 数',
  poi_food      INT    COMMENT '餐饮服务类 POI 数',
  poi_total     INT    COMMENT 'POI 总数',
  is_tou_zone   INT    COMMENT '是否分时电价区（由 e_price 标准差反推）',
  price_std     DOUBLE COMMENT '电价时序标准差',
  price_peak    DOUBLE COMMENT '峰电价',
  price_valley  DOUBLE COMMENT '谷电价',
  price_gap     DOUBLE COMMENT '峰谷价差'
)
COMMENT '分区综合维度表（E 组创新点②依赖此表）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- ----------------------------------------------------------------------
-- ⑤ 维表整合（POI 聚合 + 电价统计 + is_tou_zone 判定）
-- is_tou_zone：σ_price > 0.05 → 分时电价区（TOU），否则固定电价区（FLAT）
-- ----------------------------------------------------------------------
INSERT OVERWRITE TABLE uev_dwd.dim_zone_info
SELECT
    i.TAZID                                        AS zone_id,
    i.longitude, i.latitude, i.charge_count, i.area, i.perimeter,
    p.poi_lifestyle, p.poi_business, p.poi_food, p.poi_total,
    CASE WHEN e.price_std > 0.05 THEN 1 ELSE 0 END AS is_tou_zone,
    e.price_std,
    e.price_peak,
    e.price_valley,
    e.price_peak - e.price_valley                   AS price_gap
FROM uev_ods.inf i
LEFT JOIN uev_dwd.zone_poi_count p
       ON i.TAZID = p.zone_id
LEFT JOIN (
    SELECT
        zone_id,
        STDDEV_POP(value) AS price_std,
        MAX(value)        AS price_peak,
        MIN(value)        AS price_valley
    FROM uev_dwd.zone_hour_metric
    WHERE metric = 'e_price'
    GROUP BY zone_id
) e ON i.TAZID = e.zone_id;

-- ----------------------------------------------------------------------
-- 校验
-- ----------------------------------------------------------------------
-- SELECT COUNT(*) FROM uev_dwd.zone_hour_metric;      -- 期望 1,194,600（单指标）
-- SELECT COUNT(*) FROM uev_dwd.dim_zone_info;          -- 期望 275
-- SELECT COUNT(*) FROM uev_dwd.zone_poi_count;         -- 期望 275
-- ==============================================================================
