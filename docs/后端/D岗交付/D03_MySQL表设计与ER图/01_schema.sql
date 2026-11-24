-- =============================================================================
-- 01_schema.sql —— UrbanEV 业务库建表脚本
-- =============================================================================
-- 维护人：杨珊珊（D 岗）　| 交付物：D03 MySQL 表设计与 ER 图
--
-- 【定位】
--   1) ads_* 类表：由 Sqoop 从 Hive ADS 层导出（B 岗灌数），后端只读；
--   2) sys_* / query_log：D 岗自建，登录鉴权与审计用；
--   3) v_* 视图：后端接口只查视图，不直接查表（D08）。
--
-- 【执行】
--   mysql -u root -p < db/mysql/01_schema.sql
--   再执行 02_seed_mock.sql 灌入演示数据（B 岗真数据到位后可 TRUNCATE 重灌）
--
-- 【注意】
--   compute_time / forecast_date 等时间字段统一用 VARCHAR 存字符串，
--   避免 Sqoop 导出时 Hive TIMESTAMP → MySQL DATETIME 的类型映射坑
--   （契约 04 · 七节专门提醒过这一点）。
-- =============================================================================

CREATE DATABASE IF NOT EXISTS uev_charge
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE uev_charge;

-- -----------------------------------------------------------------------------
-- ① KPI 概览（首页 5 个指标卡）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS dashboard_kpi;
CREATE TABLE dashboard_kpi (
  id              BIGINT       NOT NULL AUTO_INCREMENT,
  dt              VARCHAR(20)  NOT NULL COMMENT '统计日期，全量统计为 ALL',
  station_count   INT          COMMENT '充电站/分区数',
  pile_count      INT          COMMENT '充电桩总数',
  avg_occupancy   DOUBLE       COMMENT '平均占用率 0-1',
  total_volume    DOUBLE       COMMENT '累计充电量 kWh',
  avg_duration    DOUBLE       COMMENT '平均充电时长（小时）',
  imbalance_zones INT          COMMENT '供需失衡分区数',
  compute_time    VARCHAR(30)  COMMENT '计算时间戳',
  PRIMARY KEY (id),
  KEY idx_dt (dt)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='KPI 概览';

-- -----------------------------------------------------------------------------
-- ② 分区占用率（热力图 / 地图）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS zone_occupancy;
CREATE TABLE zone_occupancy (
  id             BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id        VARCHAR(20) NOT NULL COMMENT '交通分区编号（= inf.csv 的 TAZID）',
  longitude      DOUBLE      COMMENT '经度 WGS84',
  latitude       DOUBLE      COMMENT '纬度 WGS84',
  avg_occupancy  DOUBLE      COMMENT '日均占用率 0-1',
  max_occupancy  DOUBLE      COMMENT '峰值占用率 0-1',
  charge_count   INT         COMMENT '充电桩数',
  poi_total      INT         COMMENT 'POI 总数',
  PRIMARY KEY (id),
  UNIQUE KEY uk_zone (zone_id),
  KEY idx_occ (avg_occupancy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分区占用率';

-- -----------------------------------------------------------------------------
-- ③ 24 小时供需曲线
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS hourly_supply_demand;
CREATE TABLE hourly_supply_demand (
  id             BIGINT NOT NULL AUTO_INCREMENT,
  hour_of_day    INT    NOT NULL COMMENT '小时 0-23',
  avg_occupancy  DOUBLE COMMENT '平均占用率',
  avg_demand     DOUBLE COMMENT '需求份额 D(t)',
  avg_supply     DOUBLE COMMENT '运力份额 S(t)',
  gap            DOUBLE COMMENT '供需差 = D - S',
  imbalance      DOUBLE COMMENT '失衡指数（归一化后）',
  PRIMARY KEY (id),
  UNIQUE KEY uk_hour (hour_of_day)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='24 小时供需曲线';

-- -----------------------------------------------------------------------------
-- ④ 供需失衡指数 ★ 创新点①
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS imbalance_index;
CREATE TABLE imbalance_index (
  id            BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id       VARCHAR(20) NOT NULL,
  longitude     DOUBLE,
  latitude      DOUBLE,
  hour_of_day   INT         COMMENT '小时 0-23',
  demand_share  DOUBLE      COMMENT '需求份额',
  supply_share  DOUBLE      COMMENT '运力份额',
  imbalance     DOUBLE      COMMENT 'I(z,t) = D - S，正值=供不应求',
  rank_no       INT         COMMENT '该时段内排名',
  PRIMARY KEY (id),
  KEY idx_zone_hour (zone_id, hour_of_day),
  KEY idx_rank (rank_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供需失衡指数';

-- -----------------------------------------------------------------------------
-- ⑤ 电价弹性 ★ 创新点②
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS price_elasticity;
CREATE TABLE price_elasticity (
  id             BIGINT NOT NULL AUTO_INCREMENT,
  price_type     VARCHAR(10) NOT NULL COMMENT 'TOU=分时电价区 FLAT=固定电价区',
  hour_of_day    INT    NOT NULL,
  avg_occupancy  DOUBLE COMMENT '平均占用率',
  zone_count     INT    COMMENT '分组内分区数',
  avg_price_gap  DOUBLE COMMENT '平均峰谷电价差',
  PRIMARY KEY (id),
  UNIQUE KEY uk_type_hour (price_type, hour_of_day)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分时电价弹性';

-- -----------------------------------------------------------------------------
-- ⑥ 需求预测 ★ 创新点③
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS demand_forecast;
CREATE TABLE demand_forecast (
  id              BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id         VARCHAR(20) NOT NULL,
  forecast_date   VARCHAR(20) NOT NULL COMMENT '预测日期 yyyy-MM-dd',
  hour_of_day     INT         NOT NULL,
  predict_volume  DOUBLE      COMMENT '预测电量 kWh',
  actual_volume   DOUBLE      COMMENT '实际电量 kWh（回测期）',
  mape            DOUBLE      COMMENT '平均绝对百分比误差（%）',
  PRIMARY KEY (id),
  KEY idx_zone_date (zone_id, forecast_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='充电需求预测';

-- -----------------------------------------------------------------------------
-- ⑦ 布点扩容建议 ★ 创新点③
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS expansion_suggestion;
CREATE TABLE expansion_suggestion (
  id              BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id         VARCHAR(20) NOT NULL,
  longitude       DOUBLE,
  latitude        DOUBLE,
  current_piles   INT         COMMENT '现有充电桩数',
  suggested_piles INT         COMMENT '建议新增充电桩数（不是总数）',
  priority        INT         COMMENT '优先级 1=最高',
  reason          VARCHAR(500) COMMENT '完整中文结论句',
  avg_occupancy   DOUBLE      COMMENT '平均占用率',
  peak_gap        DOUBLE      COMMENT '峰值缺口（失衡指数）',
  PRIMARY KEY (id),
  KEY idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='布点扩容建议';

-- -----------------------------------------------------------------------------
-- ⑧ 数据字典（前端"数据源说明"页）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS data_dictionary;
CREATE TABLE data_dictionary (
  id           BIGINT      NOT NULL AUTO_INCREMENT,
  file_name    VARCHAR(50) NOT NULL COMMENT 'CSV 文件名',
  metric_name  VARCHAR(50) COMMENT '对应业务指标',
  unit         VARCHAR(20) COMMENT '单位',
  row_count    BIGINT      COMMENT '数据行数',
  grain        VARCHAR(50) COMMENT '数据粒度',
  description  VARCHAR(500) COMMENT '说明',
  PRIMARY KEY (id),
  UNIQUE KEY uk_file (file_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据字典';

-- -----------------------------------------------------------------------------
-- ⑨ 分区×小时画像（D 岗新增读模型，给分区详情页画峰谷曲线）
--    B 岗可直接从 uev_dws.zone_hour_profile Sqoop 导出，字段一一对应
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS zone_hour_profile;
CREATE TABLE zone_hour_profile (
  id             BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id        VARCHAR(20) NOT NULL,
  hour_of_day    INT         NOT NULL,
  avg_occupancy  DOUBLE      COMMENT '该分区该小时的平均占用率',
  avg_duration   DOUBLE      COMMENT '平均充电时长（小时）',
  avg_volume     DOUBLE      COMMENT '平均电量 kWh',
  sample_days    INT         COMMENT '样本天数',
  PRIMARY KEY (id),
  UNIQUE KEY uk_zone_hour (zone_id, hour_of_day),
  KEY idx_occ (avg_occupancy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分区×小时画像';

-- -----------------------------------------------------------------------------
-- ⑩ 双口径电量偏差（D03 新增，E 岗灌数）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS volume_deviation;
CREATE TABLE volume_deviation (
  id           BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id      VARCHAR(20) NOT NULL,
  volume       DOUBLE      COMMENT '口径①上报电量 kWh',
  volume_11kw  DOUBLE      COMMENT '口径②11kW 桩折算电量 kWh',
  deviation    DOUBLE      COMMENT '偏差率 |v1-v2|/v1，0-1',
  PRIMARY KEY (id),
  UNIQUE KEY uk_zone (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='双口径电量偏差';

-- -----------------------------------------------------------------------------
-- ⑪ POI 关联分析（D03 新增，B 岗空间维表灌数）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS poi_correlation;
CREATE TABLE poi_correlation (
  id             BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id        VARCHAR(20) NOT NULL,
  poi_total      INT         COMMENT 'POI 总数',
  poi_density    DOUBLE      COMMENT 'POI 密度（个/km²）',
  pile_density   DOUBLE      COMMENT '桩密度（个/km²）',
  avg_occupancy  DOUBLE      COMMENT '平均占用率',
  PRIMARY KEY (id),
  UNIQUE KEY uk_zone (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='POI 关联分析';

-- -----------------------------------------------------------------------------
-- ⑫ 用户表（D 岗自建，D04 登录鉴权用）
--    密码存 BCrypt 密文，禁止明文（对应参考作业"6 处明文密码"的硬伤）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS sys_user;
CREATE TABLE sys_user (
  id            BIGINT       NOT NULL AUTO_INCREMENT,
  username      VARCHAR(50)  NOT NULL COMMENT '登录名',
  password_hash VARCHAR(100) NOT NULL COMMENT 'BCrypt 密文，$2a$10$...',
  real_name     VARCHAR(50)  COMMENT '真实姓名',
  role_code     VARCHAR(20)  COMMENT '角色编码，关联 sys_role.role_code',
  status        TINYINT      NOT NULL DEFAULT 1 COMMENT '1=启用 0=停用',
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_login_at DATETIME     NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统用户';

-- -----------------------------------------------------------------------------
-- ⑬ 角色表
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS sys_role;
CREATE TABLE sys_role (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  role_code   VARCHAR(20) NOT NULL COMMENT 'ADMIN / ANALYST / VIEWER',
  role_name   VARCHAR(50) NOT NULL,
  description VARCHAR(200),
  PRIMARY KEY (id),
  UNIQUE KEY uk_role_code (role_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='角色';

-- -----------------------------------------------------------------------------
-- ⑭ 接口查询日志（审计 + 缓存性能证据）
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS query_log;
CREATE TABLE query_log (
  id         BIGINT       NOT NULL AUTO_INCREMENT,
  api_path   VARCHAR(200) NOT NULL COMMENT '请求路径',
  params     VARCHAR(500) COMMENT '查询参数',
  cost_ms    INT          COMMENT '耗时毫秒',
  hit_cache  TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '1=命中缓存 0=回源查库',
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_created (created_at),
  KEY idx_path (api_path)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接口查询日志';

-- =============================================================================
-- 视图层：后端接口只读这里（D08）
-- 说明：视图定义里没有业务口径，口径全在 B 岗的 ADS 表里；
--       B 岗拿到 B10 任务后可以替换这些视图定义，只要「视图名 + 字段名」不变，
--       D 的 Mapper XML 一行都不用改。
-- =============================================================================

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
