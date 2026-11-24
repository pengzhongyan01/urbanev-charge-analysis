#!/usr/bin/env bash
# ==============================================================================
# sqoop_export.sh —— Hive ADS 7 张表 → MySQL 导出（B 岗 · 苏静）
#
# 用法：bash sqoop_export.sh
# 前置：MySQL 已建 uev_charge 库与 7 张 ads_* 表（db/mysql/01_schema.sql）
# 注意：compute_time 等时间字段用 VARCHAR 接收，避免 TIMESTAMP 类型映射坑
# ==============================================================================
set -euo pipefail

MYSQL_URI="jdbc:mysql://localhost:3306/uev_charge?useSSL=false&allowPublicKeyRetrieval=true"
MYSQL_USER="root"
MYSQL_PWD="uev123456"          # ★ 生产须走配置中心，不硬编码

export_table() {
  local hive_table="$1"
  local mysql_table="$2"
  local columns="$3"
  echo ">>> 导出 ${hive_table} -> ${mysql_table}"
  sqoop export \
    --connect "${MYSQL_URI}" \
    --username "${MYSQL_USER}" \
    --password "${MYSQL_PWD}" \
    --table "${mysql_table}" \
    --hcatalog-table "${hive_table}" \
    --hcatalog-database uev_ads \
    --m 1 \
    --columns "${columns}" \
    --input-fields-terminated-by '\001' \
    --null-string '\\N' \
    --null-non-string '\\N'
}

export_table "dashboard_kpi"         "dashboard_kpi" \
  "dt,station_count,pile_count,avg_occupancy,total_volume,avg_duration,imbalance_zones,compute_time"

export_table "zone_occupancy"       "zone_occupancy" \
  "zone_id,longitude,latitude,avg_occupancy,max_occupancy,charge_count,poi_total"

export_table "hourly_supply_demand" "hourly_supply_demand" \
  "hour_of_day,avg_occupancy,avg_demand,avg_supply,gap,imbalance"

export_table "imbalance_index"      "imbalance_index" \
  "zone_id,longitude,latitude,dt,hour_of_day,demand,supply,imbalance,rank_no"

export_table "price_elasticity"     "price_elasticity" \
  "price_type,hour_of_day,avg_occupancy,zone_count,avg_price_gap"

export_table "demand_forecast"      "demand_forecast" \
  "zone_id,forecast_date,hour_of_day,predict_volume,actual_volume,mape"

export_table "expansion_suggestion" "expansion_suggestion" \
  "zone_id,longitude,latitude,current_piles,suggested_piles,priority,reason,avg_occupancy,peak_gap"

echo ">>> 全部导出完成，请用 MySQL查询验证.sql 核对行数"
