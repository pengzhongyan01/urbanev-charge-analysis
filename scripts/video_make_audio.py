# -*- coding: utf-8 -*-
"""
旁白配音合成 + 字幕生成
运行：python scripts/video_make_audio.py

输出（到 %TEMP%/uev_video_audio/）：
  seg_01.mp3 ... seg_28.mp3   每个镜头一段旁白
  narration.json              镜头时长、旁白文本、字幕文本
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import edge_tts

OUT = Path(os.environ.get("TEMP", r"C:/Users/彭忠燕/AppData/Local/Temp")) / "uev_video_audio"
OUT.mkdir(parents=True, exist_ok=True)

VOICE = "zh-CN-XiaoxiaoNeural"
RATE = "-6%"          # 比默认略慢，贴合技术讲解
PITCH = "+0Hz"
GAP = 0.45            # 段间静音（秒）

# ── 逐镜头旁白文本 ────────────────────────────────────────────────────────
NARRATION: list[tuple[str, str]] = [
    ("L01", "各位老师好。下面是我们第 02 组的演示视频。我们的题目是《基于 ETL 的城市充电桩数据分析系统的设计与实现》。"),
    ("L02", "先用两张图看系统骨架。"),
    ("L03", "这是系统整体技术架构，从下往上分六层：数据资源、ETL 处理、数仓存储、计算分析、应用展示。右侧是技术选型：Hadoop、Hive、Spark、MySQL、Redis、Spring Boot。"),
    ("L04", "这是整体数据流向图，把数据准备、接入、ETL 处理与分析、核心功能模块、决策输出五个阶段串了起来。每个阶段都有对应的产出物和校验点。"),
    ("L05", "接着看数据从哪来。"),
    ("L06", "原始数据经 Flume 实时采集，写入 Kafka 削峰，再由 Sqoop 增量导入 Hive。每一类 CSV 对应一条采集通道，与十二张 ODS 表一一对应。"),
    ("L07", "数仓按 ODS、DWD、DWS、ADS 四层组织。DWD 做宽转长和清洗，ADS 直接产出前端和接口要用的分析结果。"),
    ("L08", "其中最关键的一层是 DWD。它把原始的分区乘小时的宽表，转成长表，一行记录一个分区在一个时刻的一个指标值，这是后续所有时空分析的基础。"),
    ("L09", "这一步的字段和 Hive 侧严格对齐，保证两条技术路线产出的数据可以互相校验。"),
    ("L10", "数据清洗是 ETL 最核心的环节。"),
    ("L11", "宽转长的做法是：repeat 把分区沿时间轴展开，tile 把时间戳平铺，最后 ravel 成一维，一行对应一个分区一个时刻一个指标。"),
    ("L12", "清洗规则按指标类型分别定义：占用率在零到一之间，时长电量价格不能为负。违反的先置为缺失值而不是直接丢弃。"),
    ("L13", "重复的时间戳，按分区、时间和指标三个键去重，只保留第一条；零值单独打标，方便后续区分「确实没有数据」和「数据本身就是零」。"),
    ("L14", "这是清洗后的实测质量结果：716 万行，越界、重复、空值全部为零。只有百分之三点三的全零值，是采集静默，我们标记保留而不删除。"),
    ("L15", "接下来是三个核心创新点。"),
    ("L16", "失衡指数定义为需求份额减去运力份额。这里强调口径：份额差消除了分区规模差异，四个桩和四百多个桩的分区才能公平比较。正值就是需要优先补点的区域。"),
    ("L17", "这里踩过一个坑：先构造全量长表再 merge，键类型不一致产生笛卡尔积，膨胀到三点二亿行撑爆内存。改成在矩阵上直接取 TOP-N，内存降到 MB 级。"),
    ("L18", "这是 C 岗绘制的失衡指数分区排名。全市 275 个分区中，峰值失衡大于零的有 56 个，占百分之二十点四，集中在 595 区、1167 区这些高需求份额的分区。"),
    ("L19", "创新点二看电价弹性。分时定价的 31 个分区，全天占用率百分之三十四点四；固定定价的 244 个分区是百分之二十六点二，相差八点二个百分点。"),
    ("L20", "这两类电价区的点云清晰分离，而且价差越大占用率越低。也就是说，拉开峰谷价差来削峰，是有数据支撑的。"),
    ("L21", "创新点三用七维特征做 KMeans 聚类，种子固定 42 保证可复现。275 个分区分成紧张型 27、过剩型 128、稳定型 79、潜力型 41。"),
    ("L22", "这是需求预测曲线，预测紧跟实际走势，只在个别峰值天略微保守。"),
    ("L23", "误差分布上，三千八百五十个回测样本的中位 MAPE 是百分之九点九，百分之七十三的样本误差低于百分之二十，长尾集中在电量极小的小分区。"),
    ("L24", "布点建议给出：全市 56 个分区存在缺口，建议新增 93 个桩，只占现有规模的百分之一点八。说明全市靠调度错峰就能解决大部分问题。"),
    ("L25", "后端使用 Spring Boot 加 MyBatis 实现，一共十六个接口。"),
    ("L26", "性能优化上用 AOP 做了缓存切面，打在 Service 层而非 Controller 层，因为 Service 返回具体的 VO，能精确还原。流程是查缓存、回源、回填三步，结果为空时不缓存，避免穿透。"),
    ("L27", "缓存 key 由方法名和全部入参做 MD5 生成。入参含五个筛选字段，改任何筛选都会换 key，不会拿到旧数据。"),
    ("L28", "这是后端十六个接口的调用关系和缓存分层。请求从 Controller 进入，Service 层负责参数校验、指标计算和缓存策略，Mapper 层只做数据访问。"),
    ("L29", "十六个接口全部 Postman 实测，响应截图都留了档。"),
    ("L30", "下面是 C 岗实现的真实页面。"),
    ("L31", "首页总览一屏掌握核心 KPI：全市 275 个分区，56 个供不应求，峰值失衡 0.1225。"),
    ("L32", "分区地图把 275 个分区按失衡程度着色，颜色越红代表越紧张。"),
    ("L33", "供需分析页给出分区级的失衡诊断和预测得分，可以逐个分区看细节。"),
    ("L34", "电价与误差页把 TOU 和 FLAT 两类分区分组对照，对应创新点二。"),
    ("L35", "需求预测页是实际值与预测值的曲线对比。"),
    ("L36", "布点建议页给出扩容优先级，直接对应实际选址决策。"),
    ("L37", "这是 Postman 的真实调用和响应。缓存统计接口显示命中率零点三三，加速比两千六百多毫秒，缓存切实生效。"),
    ("L38", "最后总结一下本项目的工作。"),
    ("L39", "本项目完成了完整的四层数仓建设；指标口径都有契约文档并做过独立复算；核心创新是供需失衡指数和七维聚类选址模型；后端十六个接口全部实测通过。数据窗口是 2022 年 9 月到 2023 年 2 月，是 UrbanEV 论文发表时可用的最新窗口。"),
    ("L40", "以上就是我们的演示，谢谢观看，欢迎老师提问。"),
]

# 镜头时长（秒）：由 measure 步骤按旁白实测时长回填，不手写
DURATION: dict[str, float] = {}

# 实测旁白时长（由 measure_durations 回填，避免人工估计误差）
MEASURED: dict[str, float] = {}


def subtitle_text(txt: str) -> str:
    """字幕：按标点切成短句，去掉书名号等噪音。"""
    txt = txt.replace("《", "").replace("》", "")
    txt = txt.replace("「", "").replace("」", "")
    return txt


async def synth_one(idx: int, code: str, text: str) -> Path:
    out = OUT / f"seg_{code}.mp3"
    if out.exists() and out.stat().st_size > 1000:
        return out
    comm = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await comm.save(str(out))
    return out


async def main() -> None:
    manifest = []
    for i, (code, text) in enumerate(NARRATION, 1):
        p = await synth_one(i, code, text)
        size = p.stat().st_size
        print(f"[{i:02d}/{len(NARRATION)}] {code}  {size/1024:6.1f} KB  {text[:24]}…")
        manifest.append({
            "code": code,
            "audio": str(p),
            "text": subtitle_text(text),
            "duration": DURATION.get(code, 12.0),
        })

    (OUT / "narration.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ {len(manifest)} 段旁白 → {OUT}")
    print(f"  旁白总字数 {sum(len(t) for _, t in NARRATION)}")


def measure_durations() -> None:
    """实测每段 mp3 时长，把镜头时长回填为「实测 + 呼吸间隙」。"""
    import subprocess
    ff = os.environ.get("FFMPEG_BIN")
    if not ff:
        try:
            import imageio_ffmpeg
            ff = imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            ff = "ffmpeg"

    manifest = json.loads((OUT / "narration.json").read_text(encoding="utf-8"))
    total = 0.0
    print(f"{'镜':5}{'旁白':>7}{'镜头':>7}{'累计':>8}")
    for it in manifest:
        out = subprocess.run([ff, "-hide_banner", "-i", it["audio"]],
                             capture_output=True, text=True).stderr
        line = [l for l in out.splitlines() if "Duration:" in l][0]
        h, mi, s = line.split("Duration:")[1].split(",")[0].strip().split(":")
        actual = float(h) * 3600 + float(mi) * 60 + float(s)
        # 镜头时长 = 旁白 + 0.6s 呼吸间隙；不足 6s 的补到 6s（避免闪屏）
        shot = max(6.0, round(actual + 0.6, 2))
        it["audio_duration"] = round(actual, 2)
        it["duration"] = shot
        total += shot
        print(f"{it['code']:5}{actual:7.1f}{shot:7.1f}{total:8.1f}")

    (OUT / "narration.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n总时长 {total:.1f}s = {total/60:.2f} min")
    # 同步回写分镜脚本里的时长表
    _sync_script(manifest, total)


def _sync_script(manifest: list[dict], total: float) -> None:
    script = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis/docs/视频/分镜脚本.md")
    if not script.exists():
        return
    lines = script.read_text(encoding="utf-8").splitlines()
    dur_map = {it["code"]: it["duration"] for it in manifest}
    out = []
    for ln in lines:
        # 形如 "**L03 · 00:26–00:46 · 20s · 架构图页**"
        m = re.match(r"^\*\*(L\d\d) · (\d\d:\d\d)[–-](\d\d:\d\d) · (\d+)s", ln)
        if m and m.group(1) in dur_map:
            code = m.group(1)
            new_d = dur_map[code]
            start = _parse_tc(m.group(2))
            end = round(start + new_d, 1)
            ln = re.sub(r"^\*\*L\d\d · ", f"**{code} · ", ln)
            ln = re.sub(r" · \d\d:\d\d[–-]\d\d:\d\d · ", f" · {_fmt_tc(start)}–{_fmt_tc(end)} · ", ln)
            ln = re.sub(r" · \d+s · ", f" · {new_d:.0f}s · ", ln)
        out.append(ln)
    script.write_text("\n".join(out), encoding="utf-8")
    print(f"  分镜脚本时长已同步 → {script}")


def _parse_tc(t: str) -> float:
    m, s = t.split(":")
    return int(m) * 60 + int(s)


def _fmt_tc(t: float) -> str:
    t = int(round(t))
    return f"{t//60:02d}:{t%60:02d}"


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "measure":
        measure_durations()
    else:
        asyncio.run(main())
