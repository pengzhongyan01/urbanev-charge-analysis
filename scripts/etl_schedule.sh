#!/usr/bin/env bash
# ==============================================================================
# 作业调度.sh —— 数仓每日 ETL 调度（B 岗 · 苏静）
#
# 用法：bash 作业调度.sh
# cron 注册（每日 02:00）：
#   0 2 * * * /bin/bash /path/to/作业调度.sh >> /var/log/uev_etl.log 2>&1
# ==============================================================================
set -euo pipefail

LOG_DIR="/var/log/uev"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/etl_$(date '+%Y%m%d').log"
exec > >(tee -a "$LOG") 2>&1

echo "===== ETL 调度开始 $(date '+%Y-%m-%d %H:%M:%S') ====="

# 1. 数据就绪校验
bash scripts/verify_data.sh || { echo "[FAIL] 数据校验失败"; exit 1; }

# 2. 宽转长 + 清洗（MR）
echo ">>> 步骤1 宽转长 + 清洗"
# hadoop jar uev-mr.jar com.uev.mr.WideToLong ...
# hadoop jar uev-mr.jar com.uev.mr.DataQualityCheck ...

# 3. DWS 汇总 + ADS 计算（Spark SQL）
echo ">>> 步骤2 DWS 汇总 + ADS 计算"
# spark-sql --master local[*] -f hadoop/spark/ads_metrics.sql

# 4. Sqoop 导出 MySQL
echo ">>> 步骤3 Sqoop 导出"
# bash B09_Sqoop导出到MySQL/sqoop_export.sh

# 5. 端到端体检
echo ">>> 步骤4 体检"
bash scripts/smoke_test.sh

echo "===== ETL 调度完成 $(date '+%Y-%m-%d %H:%M:%S') ====="
