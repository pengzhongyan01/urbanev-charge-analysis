#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_ddl.py —— 自动生成 UrbanEV 宽表的 Hive DDL
=================================================================
维护人：A（组长）　|　消费方：苏静（B 组）
交付：11/24　|　创建时间：2026-11-19

【为什么需要这个脚本】
UrbanEV 的时序数据是"宽表"：time 列 + 275 个分区列。
手写 275 个字段名不可能，本脚本自动从 CSV 表头生成完整 DDL。
直接改完贴进 Hive CLI 就能建表。

【用法】
    python3 hadoop/hive/gen_ddl.py                    # 输出全部建表语句
    python3 hadoop/hive/gen_ddl.py > ddl_all.sql      # 导出到文件
    python3 hadoop/hive/gen_ddl.py --db uev_ods       # 指定库名
    python3 hadoop/hive/gen_ddl.py --table occupancy   # 只生成某一个
"""

import argparse
import csv
import io
import os
import sys

# ----------------------------------------------------------------------
# 六个时序宽表的元信息：文件名 -> (表名, 字段类型, 中文注释)
# ----------------------------------------------------------------------
TIME_SERIES = {
    "occupancy":   ("occupancy",   "DOUBLE", "充电桩占用率"),
    "duration":    ("duration",    "DOUBLE", "充电总时长（小时）"),
    "volume":      ("volume",      "DOUBLE", "充电总电量（按桩额定功率推算，kWh）"),
    "volume-11kW": ("volume_11kw", "DOUBLE", "充电总电量（按 11kW 标准车型口径，kWh）"),
    "e_price":     ("e_price",     "DOUBLE", "电价（元/kWh）"),
    "s_price":     ("s_price",     "DOUBLE", "服务费（元/kWh）"),
}

DATA_DIR_CANDIDATES = ["data/raw", "data/dataset", "../data/raw", "../../data/raw"]

# 分区维表 inf.csv 的字段定义（不是宽表，单独处理）
INF_DDL = """
-- =====================================================================
-- 分区维表：inf.csv（275 行）
-- ⚠️ 坑：TAZID 是 STRING 类型；本表行序与时序表列序不一致，
--         join 时必须按 TAZID = zone_id 显式匹配，禁止按行号对齐
-- =====================================================================
CREATE TABLE IF NOT EXISTS {db}.inf (
  TAZID       STRING  COMMENT '交通分区编号（字符串）',
  longitude   DOUBLE  COMMENT '经度 WGS84',
  latitude    DOUBLE  COMMENT '纬度 WGS84',
  charge_count INT    COMMENT '该分区充电桩总数',
  area        DOUBLE  COMMENT '分区面积 m2',
  perimeter   DOUBLE  COMMENT '分区周长 m'
)
COMMENT '分区基础信息维表（来自 inf.csv）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');
"""


def find_data_dir():
    """定位数据目录"""
    for d in DATA_DIR_CANDIDATES:
        if os.path.isdir(d):
            return d
    return None


def read_header(data_dir, csv_name):
    """读取 CSV 表头，返回列名列表"""
    path = os.path.join(data_dir, csv_name)
    if not os.path.isfile(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        header = next(csv.reader(f))
    return header


def gen_wide_ddl(db, csv_name, table, col_type, comment, header):
    """生成宽表 DDL"""
    zone_cols = header[1:]           # 跳过 time 列
    cols = ["  `time` STRING  COMMENT '小时时间戳 yyyy-MM-dd HH:mm:ss'"]
    for c in zone_cols:
        cols.append("  `%s` %s" % (c, col_type))
    body = ",\n".join(cols)

    return f"""
-- =====================================================================
-- 宽表：{csv_name}（{len(zone_cols)} 个分区列，4,344 行数据）
-- 指标：{comment}
-- ⚠️ 列名即分区编号，建表后需 explode 成 (zone_id, hour_ts, value) 长表
-- =====================================================================
CREATE TABLE IF NOT EXISTS {db}.{table} (
{body}
)
COMMENT '{comment}（宽表，来自 UrbanEV {csv_name}）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');
"""


def gen_matrix_ddl(db):
    """邻接矩阵与距离矩阵 DDL"""
    return f"""
-- =====================================================================
-- 邻接矩阵 adj.csv（275 x 275，0/1）
-- ⚠️ 无时间维度，属静态维表；行列索引即分区编号
-- =====================================================================
CREATE TABLE IF NOT EXISTS {db}.adj_matrix (
  zone_id STRING COMMENT '行分区编号',
  `102` INT, `104` INT, `105` INT
  -- 实际 275 列，用下方脚本生成
)
COMMENT '分区邻接矩阵'
STORED AS ORC;

-- =====================================================================
-- 距离矩阵 distance.csv（275 x 275，单位推断为米）
-- ⚠️ 官方未标注单位，报告中需说明是推断值
-- =====================================================================
CREATE TABLE IF NOT EXISTS {db}.distance_matrix (
  zone_id STRING COMMENT '行分区编号',
  `102` DOUBLE, `104` DOUBLE, `105` DOUBLE
  -- 实际 275 列
)
COMMENT '分区距离矩阵'
STORED AS ORC;
"""


def main():
    parser = argparse.ArgumentParser(description="生成 UrbanEV 宽表的 Hive DDL")
    parser.add_argument("--db", default="uev_ods", help="目标数据库名")
    parser.add_argument("--data-dir", default=None, help="数据目录")
    parser.add_argument("--table", default=None, help="只生成指定表（occupancy/duration/...）")
    args = parser.parse_args()

    data_dir = args.data_dir or find_data_dir()
    if not data_dir:
        print("[错误] 找不到数据目录，请先执行 bash scripts/download_data.sh", file=sys.stderr)
        sys.exit(1)

    print("-- " + "=" * 66)
    print("-- UrbanEV Hive DDL 自动生成")
    print("-- 数据目录: %s" % os.path.abspath(data_dir))
    print("-- 目标库:   %s" % args.db)
    print("-- " + "=" * 66)

    print("""
CREATE DATABASE IF NOT EXISTS {db} COMMENT 'ODS 贴源层';
""".format(db=args.db))

    generated = 0
    for csv_name, (table, col_type, comment) in TIME_SERIES.items():
        if args.table and args.table != csv_name:
            continue
        header = read_header(data_dir, csv_name + ".csv")
        if not header:
            print("-- [跳过] %s 不存在" % csv_name)
            continue
        print(gen_wide_ddl(args.db, csv_name, table, col_type, comment, header))
        generated += 1

    if not args.table:
        print(INF_DDL.format(db=args.db))
        print(gen_matrix_ddl(args.db))

    print("-- " + "=" * 66)
    print("-- 共生成 %d 个时序宽表 DDL" % generated)
    print("--")
    print("-- 下一步：")
    print("--   1. 把输出保存为 ddl_ods.sql")
    print("--   2. 上传到 NameNode:  hdfs dfs -put ddl_ods.sql /tmp/")
    print("--   3. 执行:               beeline -u jdbc:hive2://localhost:10000 -f /tmp/ddl_ods.sql")
    print("--")
    print("-- ⚠️ DWD 层长表 DDL 见 docs/contracts/04-数仓表结构规范.md")
    print("-- " + "=" * 66)


if __name__ == "__main__":
    main()
