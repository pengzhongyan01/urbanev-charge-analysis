-- ==============================================================================
-- MySQL查询验证.sql —— Sqoop 导出后行数核对（B 岗 · 苏静）
--
-- 用法：mysql -u root -p uev_charge < MySQL查询验证.sql
-- 期望行数与 Hive ADS 侧一致（见 04_ads.sql 末尾注释）
-- ==============================================================================

USE uev_charge;

SELECT 'dashboard_kpi'         AS tbl, COUNT(*) AS rows_cnt FROM dashboard_kpi
UNION ALL SELECT 'zone_occupancy',       COUNT(*) FROM zone_occupancy
UNION ALL SELECT 'hourly_supply_demand', COUNT(*) FROM hourly_supply_demand
UNION ALL SELECT 'imbalance_index',      COUNT(*) FROM imbalance_index
UNION ALL SELECT 'price_elasticity',     COUNT(*) FROM price_elasticity
UNION ALL SELECT 'demand_forecast',      COUNT(*) FROM demand_forecast
UNION ALL SELECT 'expansion_suggestion', COUNT(*) FROM expansion_suggestion;

-- 期望结果：
-- dashboard_kpi          = 1
-- zone_occupancy         = 275
-- hourly_supply_demand   = 24
-- imbalance_index        = 200
-- price_elasticity       = 24
-- demand_forecast        = 3850
-- expansion_suggestion   = 167

-- 抽查 KPI（答辩可展示）
SELECT * FROM dashboard_kpi;

-- 抽查 TOP10 失衡分区
SELECT zone_id, hour_of_day, imbalance, rank_no
FROM imbalance_index
WHERE rank_no <= 10
ORDER BY hour_of_day, rank_no;
