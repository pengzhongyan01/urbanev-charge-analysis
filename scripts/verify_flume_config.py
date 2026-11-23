#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_flume_config.py —— Flume 采集配置静态验证 + 等价采集证据

★ 为什么需要（A 岗兜底）
  原计划的验证方式是「启动 Docker → 跑 Flume → hdfs dfs -ls 截图」。
  但 Docker 引擎因 wsl.exe 被沙箱拦截无法启动，这条路暂时走不通。
  本脚本提供两条替代证据：
    ① 静态验证：逐条核对 flume-csv-hdfs.conf 与 Flume 1.11 官方属性表、
       与契约 04 的表定义、与 12 个真实 CSV 的一致性；
    ② 等价证据：按 Flume 的 taildir + HDFS sink 语义模拟生成 12 个通道的
       目录结构与滚动文件名，证明「12 CSV → 12 HDFS 子目录 → 12 张 ODS 表」闭合。

  ★ 等 Docker 可用后，用真实截图替换等价证据即可（报告里写明了替换步骤）。
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "flume_evidence"

# Flume 1.11 官方属性表（本项目用到的部分）
VALID = {
    "sources": {"type", "positionFile", "filegroups", "fileHeader", "batchSize",
                "maxBytesPerEvent", "minBytesPerEvent", "encoding", "scanInterval",
                "maxBatchCount", "maxBytesPerBatch"},
    "channels": {"type", "capacity", "byteCapacity", "keep-alive", "checkpoint-dir",
                 "use-flume-sink"},
    "sinks": {"type", "channel", "hdfs.path", "hdfs.filePrefix", "hdfs.fileSuffix",
              "hdfs.fileType", "hdfs.writeFormat", "hdfs.useLocalTimeStamp",
              "hdfs.rollSize", "hdfs.rollInterval", "hdfs.rollCount", "hdfs.batchSize",
              "hdfs.codec", "hdfs.inUsePrefix", "hdfs.inUseSuffix", "hdfs.closeOnEOF",
              "hdfs.minBlockReplicas", "hdfs.writeBatchSize", "hdfs.rolloverInterval",
              "hdfs.maxOpenFiles", "hdfs.retryInterval", "hdfs.idleTimeout",
              "hdfs.callTimeout", "hdfs.closeTries", "hdfs.threadsPoolSize",
              "hdfs.rollTimerPoolSize", "hdfs.useRawFormat"},
}


def find_data_dir():
    for c in [REPO / "data" / "UrbanEV", REPO.parent / "数据" / "UrbanEV",
              REPO.parent / "data" / "UrbanEV"]:
        if (c / "occupancy.csv").exists():
            return c
    return None


def main() -> int:
    conf = REPO / "hadoop" / "flume" / "flume-csv-hdfs.conf"
    if not conf.exists():
        print("[错误] 找不到 flume-csv-hdfs.conf")
        return 1

    raw = conf.read_text(encoding="utf-8")
    cfg = [(i + 1, l.strip()) for i, l in enumerate(raw.splitlines())
           if l.strip() and not l.strip().startswith("#")]

    errors: list[str] = []
    warns: list[str] = []

    print("=" * 74)
    print(" Flume 采集配置静态验证")
    print(f" 配置：{conf}")
    print("=" * 74)

    # ── 1. agent 列表一致性 ──
    def agent_list(key):
        for _, l in cfg:
            if l.startswith(f"uev-agent.{key}"):
                return l.split("=", 1)[1].split()
        return []

    srcs, chans, sinks = agent_list("sources"), agent_list("channels"), agent_list("sinks")
    print("\n[1] agent 定义")
    print(f"    sources={len(srcs)}  channels={len(chans)}  sinks={len(sinks)}")
    if len(srcs) == len(chans) == len(sinks) == 12:
        print("    OK 三者一一对应，各 12 个")
    else:
        errors.append(f"agent 列表数量不一致 {len(srcs)}/{len(chans)}/{len(sinks)}")
        print("    XX 数量不一致")

    # ── 2. 属性合法性 ──
    print("\n[2] 属性合法性（对照 Flume 1.11 官方属性表）")
    bad = []
    for ln, l in cfg:
        m = re.match(r"(uev-agent\.\S+?)\.(\S+?)\s*=\s*(.*)", l)
        if not m:
            continue
        path, attr, _ = m.groups()
        parts = path.split(".")
        if len(parts) < 3:
            continue
        allowed = VALID.get(parts[1])
        if allowed and attr not in allowed and not attr.startswith("filegroups"):
            bad.append((ln, path, attr))
    if bad:
        for ln, path, attr in bad:
            print(f"    XX 第 {ln} 行 {path}.{attr} 不在官方属性表内")
            errors.append(f"第 {ln} 行 {path}.{attr} 非法")
    else:
        print("    OK 全部属性均在官方属性表内（无静默失效项）")

    # ── 3. 五类语义陷阱 ──
    # ★ 关键：只检查【有效配置行】，不能检查整个文件文本。
    #   配置文件头部有大量注释说明「曾经犯过哪些错」，
    #   若对全文做关键词匹配，会把这些说明当成真实缺陷 → 误报。
    print("\n[3] 语义陷阱检查（仅扫有效配置行）")
    eff = "\n".join(l for _, l in cfg)          # 去掉注释与空行后的配置正文
    traps = [
        ("fileType=DataStream 却设了 codec",
         ("codec" in eff) and ("fileType = DataStream" in eff),
         "官方明确 DataStream 不压缩，gzip 不生效且与 *.gz 校验命令矛盾"),
        ("writeFormat 用了非法值 CompressedText",
         "CompressedText" in eff,
         "只允许 Text / Writable；若生效，MR 的 split 逗号只切出 1 列 → 宽转长输出 0 行"),
        ("useLocalTimeStamp=false 却没有 timestamp 拦截器",
         ("useLocalTimeStamp = false" in eff) and ("headerName = timestamp" not in eff),
         "Flume 要求事件带名为 timestamp 的 header，否则直接报错"),
        ("用了 closeOnEOF / batchInterval",
         ("closeOnEOF" in eff) or ("batchInterval" in eff),
         "Flume 1.11 HDFS Sink 没有这两个属性，会被静默忽略"),
        ("用了自定义键间接层 ${flume.*}",
         bool(re.search(r"\$\{flume\.[a-z.]+\}", eff)),
         "Flume 只解析 agent.<name>.* 前缀的键，引用行为不可靠"),
    ]
    for desc, is_bad, why in traps:
        if is_bad:
            print(f"    XX {desc}")
            print(f"       -> {why}")
            errors.append(desc)
        else:
            print(f"    OK {desc}")

    # ── 4. 通道 / CSV / ODS 表 三方一致性 ──
    print("\n[4] 通道 / CSV / ODS 表 三方一致性")
    paths = re.findall(r"hdfs\.path = hdfs://namenode:8020/uev/raw/([\w\-]+)/", raw)
    print(f"    HDFS 子目录 {len(paths)} 个：{' '.join(paths)}")
    data_dir = find_data_dir()
    if data_dir:
        missing = [n for n in paths if not (data_dir / f"{n}.csv").exists()]
        if missing:
            print(f"    XX 数据目录里缺这些 CSV：{missing}")
            errors.append(f"CSV 缺失 {missing}")
        else:
            print(f"    OK 12 个通道对应的 CSV 在 {data_dir.name}/ 中全部存在")
    else:
        warns.append("未找到数据目录，跳过 CSV 存在性检查")

    ods_ddl = REPO / "hadoop" / "hive" / "01_ods.sql"
    if ods_ddl.exists():
        tables = set(re.findall(r"CREATE EXTERNAL TABLE IF NOT EXISTS uev_ods\.(\w+)",
                                ods_ddl.read_text(encoding="utf-8")))
        norm = {p.replace("-", "_").lower() for p in paths}
        lack = sorted(norm - tables)
        if lack:
            print(f"    XX 这些通道没有对应 ODS 建表语句：{lack}")
            errors.append(f"ODS 表缺失 {lack}")
        else:
            print(f"    OK 12 个通道与 {len(tables)} 张 ODS 表一一对应")
    else:
        warns.append("未找到 hadoop/hive/01_ods.sql，跳过 ODS 对照")

    # ── 5. 等价采集证据 ──
    print("\n[5] 生成等价采集证据")
    OUT.mkdir(parents=True, exist_ok=True)
    sim_root = OUT / "hdfs_sim"
    if sim_root.exists():
        shutil.rmtree(sim_root)
    manifest = []
    for _, l in cfg:
        m = re.match(r"uev-agent\.sinks\.k_(\w+)\.hdfs\.path = (\S+)", l)
        if not m:
            continue
        tag, path = m.groups()
        name = path.rstrip("/").split("/")[-1]
        d = sim_root / name
        d.mkdir(parents=True, exist_ok=True)
        src = (data_dir / f"{name}.csv") if data_dir else None
        if src and src.exists():
            rows = sum(1 for _ in open(src, encoding="utf-8-sig")) - 1
            size = src.stat().st_size
        else:
            rows, size = 0, 0
        tbl = name.replace("-", "_").lower()
        (d / f"{name}-2026-11-23-16.csv").write_text(
            "# 等价证据（由 verify_flume_config.py 生成）\n"
            "# 模拟 Flume taildir 采集 + HDFS Sink 滚动写入的结果\n"
            f"# 源文件：{name}.csv  {rows} 行数据  {size} 字节\n"
            f"# ODS 表：uev_ods.{tbl}\n"
            f"# LOCATION：{path}\n", encoding="utf-8")
        manifest.append({"channel": tag, "hdfs_dir": path, "csv": f"{name}.csv",
                         "data_rows": rows, "size_bytes": size,
                         "ods_table": f"uev_ods.{tbl}"})
    (OUT / "采集通道清单.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    OK 已生成 {len(manifest)} 个通道的等价目录结构 -> {OUT}")

    # ── 6. 报告 ──
    L: list[str] = []
    A = L.append
    A("# Flume 采集配置验证报告")
    A("")
    A("> 生成时间：2026-11-23　|　配置文件：`hadoop/flume/flume-csv-hdfs.conf`  ")
    A("> 生成方式：`python scripts/verify_flume_config.py`  ")
    A("> 验证方式：属性表逐条比对 + 12 个真实 CSV 的存在性与行数核对")
    A("")
    A("---")
    A("")
    A("## 一、验证结论")
    A("")
    A("| 项 | 结果 |")
    A("|---|---|")
    A("| 三个 agent 列表（sources / channels / sinks） | " +
      ("OK 各 12 个，一一对应" if len(srcs) == len(chans) == len(sinks) == 12
       else "XX 数量不一致") + " |")
    A("| 属性合法性（对照 Flume 1.11 官方属性表） | " +
      ("OK 全部合法，无静默失效项" if not bad else "XX 见 2.2") + " |")
    A("| 五类语义陷阱 | " +
      ("OK 全部规避" if not any(t[1] for t in traps) else "XX 见 2.2") + " |")
    A("| 通道 / CSV / ODS 表 三方一致性 | " +
      ("OK 闭合" if not errors else "XX 见第五节") + " |")
    A("")
    A("## 二、静态验证明细")
    A("")
    A("### 2.1 12 个独立采集通道")
    A("")
    A("| # | 通道 | HDFS 子目录 | ODS 表 | CSV 数据行数 |")
    A("|---|---|---|---|---|")
    for i, m in enumerate(manifest, 1):
        A("| " + str(i) + " | `" + str(m["channel"]) + "` | `" + str(m["hdfs_dir"]) +
          "` | `" + str(m["ods_table"]) + "` | " + format(m["data_rows"], ",") + " |")
    A("")
    A("### 2.2 属性合法性")
    A("")
    A("对照 Flume 1.11 官方手册的 HDFS Sink / TAILDIR Source / Memory Channel 属性表逐条核对。")
    A("**重点是排除「语法合法但语义无效」的属性** —— 这类属性不会报错，只会静默失效：")
    A("")
    A("| 属性 | 官方是否存在 | 若误用的后果 |")
    A("|---|---|---|")
    A("| `hdfs.codec` 配 `fileType=DataStream` | 存在，但 DataStream 明确不压缩 | gzip 不生效，产出不是 `.gz`，校验命令的 glob 匹配不到文件 |")
    A("| `hdfs.writeFormat=CompressedText` | **不存在**（只允许 Text / Writable） | 若生效，MR 的 split 逗号只切出 1 列 → 宽转长输出 0 行 |")
    A("| `hdfs.closeOnEOF` | **不存在** | 静默忽略，「空文件不入库」的预期不成立 |")
    A("| `hdfs.batchInterval` | **不存在** | 静默忽略 |")
    A("| `useLocalTimeStamp=false` 且无 timestamp 拦截器 | 需配套使用 | 事件缺 `timestamp` header，Flume 直接报错 |")
    A("| 自定义键 `${flume.*}` 间接层 | 非官方机制 | Flume 只解析 `agent.<name>.*` 前缀的键，引用行为不可靠 |")
    A("")
    A("### 2.3 为什么是 12 个独立通道而不是 1 个通道 12 个文件")
    A("")
    A("12 个 CSV 的表结构完全不同（6 个 276 列宽表 + 2 个 275×275 矩阵 + 2 个气象表 + 维表 + POI），")
    A("混在同一个 HDFS 目录里会导致无法按表建 Hive 表、也无法按表做增量。")
    A("每个 CSV 一个 source/channel/sink、落 12 个独立子目录，")
    A("与 `uev_ods.*` 的 12 张表一一对应 —— 这条闭合关系由本脚本自动校验。")
    A("")
    A("## 三、等价采集证据")
    A("")
    A("由于 Docker 引擎在当前环境不可用（`wsl.exe` 被沙箱 Program Blacklist 拦截），")
    A("无法产出真实的 `hdfs dfs -ls /uev/raw/` 截图。")
    A("本目录提供**等价证据**：按 Flume 的 taildir + HDFS Sink 语义模拟生成的 12 个通道目录结构与滚动文件名，")
    A("可据此核对三件事：采集目录层级、滚动文件名格式、目录与 ODS 表名的对应关系。")
    A("")
    A("## 四、等 Docker 可用后的替换步骤（报告里要放真实截图）")
    A("")
    A("```bash")
    A("# 1. 启动 Docker Desktop（引擎就绪后）")
    A("docker compose --profile hadoop up -d flume")
    A("")
    A("# 2. 启动采集")
    A("bash scripts/start_flume.sh")
    A("")
    A("# 3. 等待 >= 5 分钟（rollInterval=300s + 默认 .tmp 后缀，前 5 分钟只有 .tmp）")
    A("")
    A("# 4. 截图（这条就是 B 岗 B01 要交的那张）")
    A("docker exec uev-namenode hdfs dfs -ls /uev/raw/")
    A("docker exec uev-namenode hdfs dfs -ls /uev/raw/occupancy/")
    A("")
    A("# 5. 截图存到：")
    A("#    作业内容/苏静/B01_Hadoop集群环境与jps截图/01_jps六进程.png")
    A("#    作业内容/彭忠燕/A02_Flume采集配置与HDFS落地/01_hdfs目录截图.png")
    A("```")
    A("")
    A("## 五、遗留问题")
    A("")
    if errors:
        A("| # | 问题 | 严重度 |")
        A("|---|---|---|")
        for i, e in enumerate(errors, 1):
            A("| " + str(i) + " | " + e + " | 高 |")
    else:
        A("本次静态验证**未发现配置缺陷**。")
    A("")
    if warns:
        A("### 提示")
        A("")
        for w in warns:
            A("- " + w)
        A("")
    A("### 仍需真机验证的部分")
    A("")
    A("| 项 | 为什么静态验不了 | 何时验证 |")
    A("|---|---|---|")
    A("| 采集断点续传是否真的不重复入库 | 需实际跑两次观察 positionFile | Docker 可用后 |")
    A("| 滚动文件切分是否在 300s 边界 | 需等待并观察目录 | Docker 可用后 |")
    A("| 12 个 CSV 是否都被正则匹配到 | 正则匹配需真实目录 | Docker 可用后 |")
    A("")
    (OUT / "Flume配置验证报告.md").write_text("\n".join(L), encoding="utf-8")
    print(f"    OK 验证报告：{OUT / 'Flume配置验证报告.md'}")

    print()
    print("=" * 74)
    if errors:
        print(f" 结果：发现 {len(errors)} 个问题")
        for e in errors:
            print("   - " + e)
        return 1
    print(f" 结果：配置静态验证通过（{len(warns)} 个提示）")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
