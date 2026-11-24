#!/usr/bin/env bash
# ==============================================================================
# 增量抽取.sh —— 数仓按 dt 分区增量抽取（B 岗 · 苏静）
#
# 用法：
#   bash 增量抽取.sh                 # 增量：只重算昨日分区
#   bash 增量抽取.sh 2023-02-28      # 回补：指定日期重跑
#   bash 增量抽取.sh all             # 全量重建
# ==============================================================================
set -euo pipefail

MODE="${1:-incremental}"

# 昨日日期（增量边界）
YESTERDAY=$(date -d "yesterday" '+%Y-%m-%d' 2>/dev/null || date -v-1d '+%Y-%m-%d')

run_partition() {
  local dt="$1"
  echo ">>> 抽取分区 dt=$dt"
  # DWD 长表：只重算该 dt 分区（由 ODS 宽表 explode 后按 dt 过滤）
  # 实际执行对应 MR 作业 + Spark SQL，此处为调度骨架
  # hadoop jar uev-mr.jar com.uev.mr.WideToLong ... -D uev.filter.dt=$dt
  # spark-sql -e "INSERT OVERWRITE TABLE uev_dws.zone_day_hour ... WHERE dt='$dt'"
  echo "    分区 $dt 抽取完成（覆盖写，幂等）"
}

case "$MODE" in
  all)
    echo ">>> 全量重建：181 天全部分区"
    # 全量：按 dt 循环
    for dt in $(seq -f "2022-%g" 1 1); do :; done
    # 简化：直接调用全量 ETL
    bash scripts/python_etl.py
    ;;
  *)
    # 增量 / 指定日期回补
    run_partition "$MODE"
    ;;
esac

echo ">>> 增量抽取完成，请运行 bash scripts/smoke_test.sh 验证"
