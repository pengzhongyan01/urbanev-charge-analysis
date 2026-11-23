#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_ods_ddl.py —— 从真实 CSV 表头自动生成全部 12 张 ODS 表的建表语句

★ 为什么要有这个（A 岗兜底）
  契约 04《数仓表结构规范》里 uev_ods 只定义了 1 张表（occupancy），
  而 Flume 配置有 12 个独立采集通道 —— 契约缺 11 张表的建表语句，
  B 岗若照契约建表，11 个通道的 HDFS 目录没有对应的表可用。
  本脚本从 12 个 CSV 的**真实表头**生成完整 DDL，保证「表结构 = 数据实际结构」。

★ 解决的三个技术难点
  1. 275 个分区列手写不可行 → 从 CSV 表头自动展开
  2. 矩阵表（adj / distance）是 275×275，列名是数字 → 必须反引号包裹
  3. 各 CSV 的列名类型不一致（TAZID / time / 数字 / 经纬度）→ 按列名模式推断类型

用法：
  python scripts/gen_ods_ddl.py                  # 输出到 stdout
  python scripts/gen_ods_ddl.py --out hadoop/hive/01_ods.sql
  python scripts/gen_ods_ddl.py --check          # 只做类型推断检查，不生成
"""
from __future__ import annotations
import argparse, csv, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ── 12 个 CSV 的元信息：HDFS 子目录名 / 中文名 / 数据形态 / 特殊处理 ──
SPEC = [
    ("occupancy",       "分区小时占用率",       "wide",  "充电桩占用率（比例 0~1）"),
    ("duration",        "分区小时充电总时长",   "wide",  "充电总时长（小时）"),
    ("volume",          "分区小时充电总电量",   "wide",  "充电总电量（桩额定功率口径，kWh）"),
    ("volume-11kW",     "分区小时充电总电量(11kW口径)", "wide", "充电总电量（11kW 标准车型口径，kWh）"),
    ("e_price",         "分区小时电价",         "wide",  "电价（元/kWh）"),
    ("s_price",         "分区小时服务费",       "wide",  "服务费（元/kWh）"),
    ("inf",             "分区维表",             "inf",   "分区坐标、桩数、面积、周长"),
    ("poi",             "兴趣点表",             "poi",   "POI 类别与经纬度"),
    ("adj",             "分区邻接矩阵",         "matrix","分区邻接关系（275×275）"),
    ("distance",        "分区距离矩阵",         "matrix","分区间距离（275×275）"),
    ("weather_airport", "宝安机场气象站",       "weather","逐小时气象观测"),
    ("weather_central", "福田气象站",           "weather","逐小时气象观测"),
]

DATA_CANDIDATES = [
    REPO / "data" / "UrbanEV", REPO / "data" / "raw",
    REPO.parent / "数据" / "UrbanEV", REPO.parent / "data" / "UrbanEV",
    REPO.parent.parent / "数据" / "UrbanEV",
]

HIVE_TYPES = {
    "int": "BIGINT", "float": "DOUBLE", "str": "STRING",
}


def find_data_dir() -> Path | None:
    for c in DATA_CANDIDATES:
        if c.is_dir() and (c / "occupancy.csv").exists():
            return c
    return None


def infer_type(col: str) -> str:
    """按列名模式推断 Hive 类型"""
    c = col.strip()
    low = c.lower()
    if low in ("time", "timestamp", "datetime", "date", "hour_ts"):
        return "STRING"
    if low in ("longitude", "latitude", "lon", "lat"):
        return "DOUBLE"
    if low in ("charge_count", "area", "perimeter", "primary_types", "type", "poi_type"):
        # area/perimeter 实测是浮点，用 DOUBLE 更安全
        if low in ("area", "perimeter"):
            return "DOUBLE"
        return "STRING" if low in ("primary_types", "type", "poi_type") else "INT"
    if c.isdigit():                       # 数字列名 → 分区号
        return "INT"
    return "STRING"


def col_def(col: str) -> str:
    """生成列定义，数字列名必须加反引号"""
    c = col.strip()
    t = infer_type(c)
    if c.isdigit():
        return f"  `{c}` {t}"
    return f"  {c} {t}"


def read_header(path: Path) -> list[str]:
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        rdr = csv.reader(f)
        return next(rdr)


def build_ddl(data_dir: Path) -> tuple[str, list[tuple[str, int, str]]]:
    parts: list[str] = []
    stats: list[tuple[str, int, str]] = []

    parts.append("""-- ==============================================================================
-- 01_ods.sql —— ODS 贴源层建表语句（12 张表）
--
-- 生成方式：python scripts/gen_ods_ddl.py
-- ★ 本文件由脚本从【真实 CSV 表头】自动生成，不是手写。
--   原因：6 个时序宽表各有 275 个分区列（合计 1,650 列），
--   手写必然出错且无法与数据对齐；矩阵表更是 275×275 = 75,625 列。
--
-- 与 Flume 的对应关系（hadoop/flume/flume-csv-hdfs.conf 的 12 个独立通道）：
--   HDFS  /uev/raw/<表名>/   ←→   uev_ods.<表名>
--
-- ★ 建表顺序：先建本文件，再执行 02_dwd.sql / 03_dws.sql / 04_ads.sql
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS uev_ods;
USE uev_ods;
""")

    for name, cn, kind, desc in SPEC:
        csv_name = f"{name}.csv"
        f = data_dir / csv_name
        if not f.exists():
            parts.append(f"-- ⚠ 跳过 {name}：未找到 {csv_name}")
            continue
        header = read_header(f)
        cols = header[1:] if header and header[0].strip().lower() in ("time", "timestamp") else header

        # 第一个字段是 time（时序宽表）或 TAZID（维表/矩阵）
        first = header[0].strip()
        if kind == "wide":
            first_col = "  time STRING COMMENT '小时时间戳 yyyy-MM-dd HH:mm:ss'"
            body = [first_col] + [col_def(c) for c in cols]
            comment = f"'{cn}（{desc}）'"
            props = "TBLPROPERTIES ('skip.header.lines.count'='1');"
        elif kind == "inf":
            body = [
                "  TAZID STRING COMMENT '分区编号'",
                "  longitude DOUBLE COMMENT '经度'",
                "  latitude DOUBLE COMMENT '纬度'",
                "  charge_count INT COMMENT '充电桩数'",
                "  area DOUBLE COMMENT '分区面积'",
                "  perimeter DOUBLE COMMENT '分区周长'",
            ]
            comment = f"'{cn}（{desc}）'"
            props = "TBLPROPERTIES ('skip.header.lines.count'='1');"
        elif kind == "poi":
            # 源文件只有 3 列（无 ID 列），按契约 01 附录说明需自行生成自增主键
            body = [
                "  poi_id BIGINT COMMENT '自增主键（源文件无 ID 列，建表后用 ROW_NUMBER() 生成）'",
                "  primary_types STRING COMMENT '兴趣点类别（仅 3 类）'",
                "  longitude DOUBLE COMMENT '经度'",
                "  latitude DOUBLE COMMENT '纬度'",
            ]
            comment = f"'{cn}（{desc}）'"
            props = "TBLPROPERTIES ('skip.header.lines.count'='1');"
        elif kind == "matrix":
            body = [col_def(c) for c in cols]
            comment = f"'{cn}（{desc}）'"
            props = "TBLPROPERTIES ('skip.header.lines.count'='1');"
        else:  # weather —— 真实表头为 time / T / P0 / P / U / nRAIN（气象缩写）
            body = [
                "  time STRING COMMENT '观测时间'",
                "  T DOUBLE COMMENT '气温 T ℃'",
                "  P0 DOUBLE COMMENT '海平面气压 P0 hPa'",
                "  P DOUBLE COMMENT '站点气压 P hPa'",
                "  U DOUBLE COMMENT '相对湿度 U %'",
                "  nRAIN DOUBLE COMMENT '降水量 nRAIN mm'",
                "  weather STRING COMMENT '天气现象'",
            ]
            comment = f"'{cn}（{desc}）'"
            props = "TBLPROPERTIES ('skip.header.lines.count'='1');"

        loc = f"'/uev/raw/{name}'"
        # ★ Hive 表名不能带连字符：volume-11kW.csv → 表名 volume_11kw
        #   （与契约 02 的 metric 取值 'volume_11kw' 保持一致）
        tbl = name.replace("-", "_").lower()
        parts.append(f"""-- ----------------------------------------------------------------------
-- {name}.csv —— {cn}
-- 表名：uev_ods.{tbl}　|　列数：{len(body)}　|　数据形态：{kind}
-- LOCATION 与 Flume 的 hdfs.path 严格对应
-- ----------------------------------------------------------------------
CREATE EXTERNAL TABLE IF NOT EXISTS uev_ods.{tbl} (
{",\n".join(body)}
)
COMMENT {comment}
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION {loc}
{props}
""")
        stats.append((tbl, len(body), kind))

    parts.append("""-- ==============================================================================
-- 校验
-- ==============================================================================
-- SELECT COUNT(*) FROM uev_ods.occupancy;        -- 期望 4344（数据行，不含表头）
-- SELECT COUNT(*) FROM uev_ods.inf;              -- 期望 275
-- SELECT COUNT(*) FROM uev_ods.poi;              -- 期望 712135
-- SELECT COUNT(*) FROM uev_ods.adj;              -- 期望 275（矩阵行数 = 分区数）
-- ==============================================================================
""")
    return "\n".join(parts), stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    data_dir = Path(args.data) if args.data else find_data_dir()
    if not data_dir:
        print("[错误] 找不到数据目录，先跑 scripts/download_data.sh")
        return 1

    ddl, stats = build_ddl(data_dir)

    if args.check:
        print("=" * 70)
        print(" ODS 表结构推断检查")
        print("=" * 70)
        for name, ncol, kind in stats:
            print(f"  uev_ods.{name:18s} {ncol:>4d} 列  ({kind})")
        print()
        print(f"  合计 {len(stats)} 张表")
        return 0

    if args.out:
        out = Path(args.out) if Path(args.out).is_absolute() else REPO / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(ddl, encoding="utf-8")
        print(f"[完成] 已写入 {out}（{len(ddl):,} 字符）")
        for name, ncol, kind in stats:
            print(f"    uev_ods.{name:18s} {ncol:>4d} 列")
    else:
        sys.stdout.write(ddl)
    return 0


if __name__ == "__main__":
    sys.exit(main())
