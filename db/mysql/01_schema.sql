-- =============================================================================
-- MySQL 业务库表结构
-- =============================================================================
-- 维护人：杨珊珊（D 组）　|　骨架由 A（组长）提供，2026-11-19
--
-- 【定位】
--   这些表由 Sqoop 从 Hive ADS 层导出，前端通过后端 API 读取。
--   表结构与 uev_ads.* 一一对应，字段名用驼峰，映射见 @Table / Mapper XML。
--
-- 【执行】
--   mysql -u root -p < db/mysql/01_schema.sql
--   （Docker 模式下会自动执行：db/mysql 挂载到 /docker-entrypoint-initdb.d）
--
-- 【注意】
--   Sqoop 导出时 compute_time 等时间字段用 VARCHAR 存字符串，
--   避免 Hive TIMESTAMP → MySQL DATETIME 的类型映射坑。
-- =============================================================================

CREATE DATABASE IF NOT EXISTS uev_charge
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_general_ci;

USE uev_charge;

-- -----------------------------------------------------------------------------
-- ① KPI 概览（前端首页 5 个指标卡）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dashboard_kpi (
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
-- ② 分区占用率（前端热力图 / 地图）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS zone_occupancy (
  id             BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id        VARCHAR(20) NOT NULL COMMENT '交通分区编号',
  longitude      DOUBLE      COMMENT '经度 WGS84',
  latitude       DOUBLE      COMMENT '纬度 WGS84',
  avg_occupancy  DOUBLE      COMMENT '日均占用率',
  max_occupancy  DOUBLE      COMMENT '峰值占用率',
  charge_count   INT         COMMENT '充电桩数',
  poi_total      INT         COMMENT 'POI 总数',
  PRIMARY KEY (id),
  UNIQUE KEY uk_zone (zone_id),
  KEY idx_occ (avg_occupancy)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分区占用率';

-- -----------------------------------------------------------------------------
-- ③ 24 小时供需曲线（前端折线图）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS hourly_supply_demand (
  id             BIGINT NOT NULL AUTO_INCREMENT,
  hour_of_day    INT    NOT NULL COMMENT '小时 0-23',
  avg_occupancy  DOUBLE COMMENT '平均占用率',
  avg_demand     DOUBLE COMMENT '需求份额',
  avg_supply     DOUBLE COMMENT '运力份额',
  gap            DOUBLE COMMENT '供需差',
  imbalance      DOUBLE COMMENT '失衡指数',
  PRIMARY KEY (id),
  UNIQUE KEY uk_hour (hour_of_day)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='24 小时供需曲线';

-- -----------------------------------------------------------------------------
-- ④ 供需失衡指数（前端柱状图）★ 创新点①
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS imbalance_index (
  id            BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id       VARCHAR(20) NOT NULL,
  longitude     DOUBLE,
  latitude      DOUBLE,
  hour_of_day   INT         COMMENT '小时 0-23',
  demand_share  DOUBLE      COMMENT '需求份额',
  supply_share  DOUBLE      COMMENT '运力份额',
  imbalance     DOUBLE      COMMENT 'I(z,t) = D - S',
  rank_no       INT         COMMENT '该时段内排名',
  PRIMARY KEY (id),
  KEY idx_zone_hour (zone_id, hour_of_day),
  KEY idx_rank (rank_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='供需失衡指数';

-- -----------------------------------------------------------------------------
-- ⑤ 电价弹性（前端双曲线图）★ 创新点②
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS price_elasticity (
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
-- ⑥ 需求预测（前端预测曲线）★ 创新点③
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS demand_forecast (
  id              BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id         VARCHAR(20) NOT NULL,
  forecast_date   VARCHAR(20) NOT NULL COMMENT '预测日期 yyyy-MM-dd',
  hour_of_day     INT         NOT NULL,
  predict_volume  DOUBLE      COMMENT '预测电量 kWh',
  actual_volume   DOUBLE      COMMENT '实际电量 kWh（回测期）',
  mape            DOUBLE      COMMENT '平均绝对百分比误差',
  PRIMARY KEY (id),
  KEY idx_zone_date (zone_id, forecast_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='充电需求预测';

-- -----------------------------------------------------------------------------
-- ⑦ 布点扩容建议（前端建议看板）★ 创新点③
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS expansion_suggestion (
  id              BIGINT      NOT NULL AUTO_INCREMENT,
  zone_id         VARCHAR(20) NOT NULL,
  longitude       DOUBLE,
  latitude        DOUBLE,
  current_piles   INT         COMMENT '现有充电桩数',
  suggested_piles INT         COMMENT '建议新增充电桩数',
  priority        INT         COMMENT '优先级 1=最高',
  reason          VARCHAR(500) COMMENT '文字结论',
  avg_occupancy   DOUBLE      COMMENT '平均占用率',
  peak_gap        DOUBLE      COMMENT '峰值缺口（失衡指数）',
  PRIMARY KEY (id),
  KEY idx_priority (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='布点扩容建议';

-- -----------------------------------------------------------------------------
-- ⑧ 数据字典（前端"数据源说明"页）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_dictionary (
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
-- ⑨ 查询日志（可选，答辩时展示"系统可审计"）
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS query_log (
  id          BIGINT      NOT NULL AUTO_INCREMENT,
  api_path    VARCHAR(200) NOT NULL COMMENT '请求路径',
  params      VARCHAR(500) COMMENT '查询参数',
  cost_ms     INT         COMMENT '耗时毫秒',
  hit_cache   TINYINT(1)  DEFAULT 0 COMMENT '是否命中缓存',
  created_at  DATETIME    DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='接口查询日志';
