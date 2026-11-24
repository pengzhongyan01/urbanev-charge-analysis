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
    # (镜头号, 旁白)
    ("L01", "各位老师好。下面是我们第 02 组的演示视频。我们的题目是《基于 ETL 的城市充电桩数据分析系统的设计与实现》。"),
    ("L02", "首先介绍数据从哪来，以及怎么流进系统。"),
    ("L03", "原始数据通过 Flume 实时采集，先写入 Kafka 做削峰，再由 Sqoop 增量导入 Hive 落地。Flume 的采集通道配置和验证过程我们都留存了证据。这里每一类 CSV 对应一条独立的采集通道，和十二张 ODS 表一一对应。"),
    ("L04", "数仓按 ODS、DWD、DWS、ADS 四层组织。ODS 贴源存放，DWD 做宽转长和清洗，DWS 按分区和日期汇总，ADS 直接产出前端和接口要用的分析结果。"),
    ("L05", "其中最关键的一层是 DWD。它把原始的分区乘小时的宽表，转成长表，一行记录一个分区在一个时刻的一个指标值，这是后续所有时空分析的基础。"),
    ("L06", "这一步的字段和 Hive 侧严格对齐，保证两条技术路线产出的数据可以互相校验。"),
    ("L07", "数据清洗是整个 ETL 最核心的环节，直接决定分析结论是否可信。"),
    ("L08", "宽转长的实现方式是，先用 repeat 把分区编号沿时间轴重复展开，再用 tile 把时间戳平铺，最后 ravel 成一维，一行对应一个分区、一个时刻、一个指标。"),
    ("L09", "清洗规则按指标类型分别定义。占用率必须在零到一之间，时长和电量不能为负，价格同样不能为负。违反规则的先置为缺失值，而不是直接丢弃，避免把可以修复的数据扔掉。"),
    ("L10", "重复的时间戳，按分区、时间和指标三个键去重，只保留第一条；零值单独打标，方便后续区分「确实没有数据」和「数据本身就是零」。"),
    ("L11", "这是清洗之后的实测质量结果，全过程都有日志留存，可以逐条追溯。"),
    ("L12", "接下来是本项目最核心的创新点，供需失衡指数。"),
    ("L13", "失衡指数定义为需求份额减去运力份额。这里必须强调口径：我们采用的是份额差，而不是绝对差值。因为份额差消除了分区的规模差异，四个桩的分区和四百多个桩的分区才能公平比较。正值代表这个分区的需求份额超过了运力份额，是需要优先补点的区域。"),
    ("L14", "实现上我们踩过一个坑。如果按常规做法先构造全量长表再 merge，因为键类型不一致会产生笛卡尔积，实测膨胀到三点二亿行，直接撑爆内存。最后改成在矩阵上直接取 TOP-N，先定位扁平索引再反解出分区和时间，内存降到 MB 级。另外这里取的是 TOP 2000 而不是 TOP 200，否则榜单会被少数分区的多个时段占满，失去横向可比性。"),
    ("L15", "这是失衡指数排名前二十的分区，以及由此生成的布点建议优先级分布。"),
    ("L16", "后端使用 Spring Boot 加 MyBatis 实现，一共十六个接口。"),
    ("L17", "性能优化上，我们用 AOP 做了一个缓存切面。切面打在 Service 层而不是 Controller 层，因为 Controller 的返回值是泛型，反序列化时拿不到真实类型；打在 Service 上返回的是具体的 VO，能精确还原。流程分三步：先查缓存，命中直接返回；没有命中就回源执行；最后把结果回填缓存。而且结果为空时不做缓存，避免缓存穿透。"),
    ("L18", "缓存 key 的设计是关键。它由方法名和全部入参做 MD5 生成。入参里包含五个筛选字段，所以改任何筛选条件都会换 key，不会出现「改了筛选还拿到旧数据」这个缓存 bug。"),
    ("L19", "这十六个接口全部经过 Postman 实测，响应截图都留了档。"),
    ("L20", "下面进入运行演示环节。以下展示的都是真实运行结果。"),
    ("L21", "首页大屏展示核心 KPI。全市 275 个分区中，有 56 个处于供不应求状态，峰值分区的失衡指数是 0.1225。右侧是供不应求指数前十名的分区。"),
    ("L22", "分区地图大屏把 275 个分区按失衡程度着色，颜色越红代表越紧张，越偏蓝越充裕。"),
    ("L23", "供需失衡大屏结合了 24 小时供需曲线，可以看出每天哪些时段整体最紧张。峰值出现在凌晨 1 点。"),
    ("L24", "布点建议大屏给出新增充电桩的优先级排序，直接对应实际的选址决策。总体建议新增 93 个桩，只占现有规模的百分之一点八，说明全市靠调度和错峰就能解决大部分问题，真正需要建桩的是少数高失衡分区。"),
    ("L25", "这是 Postman 的真实调用和响应。可以看到接口返回了分区的失衡详情，缓存统计接口也确认了缓存切实生效。"),
    ("L26", "最后总结一下本项目的工作。"),
    ("L27", "本项目完成了完整的四层数据仓库建设；所有指标口径都有契约文档，并且做过独立复算，可以交叉验证；核心创新是供需失衡指数和七维聚类选址模型；后端十六个接口全部实测通过，并实现了缓存切面加 Redis 的加速方案。需要说明的是，数据窗口是 2022 年 9 月到 2023 年 2 月，这是 UrbanEV 论文发表时可用的最新窗口，而且包含价格维度，是我们选择它的原因。"),
    ("L28", "以上就是我们的演示，谢谢观看，欢迎老师提问。"),
]

# 镜头时长（秒）：以旁白实测时长为准 + 呼吸间隙；由 measure 步骤回填
DURATION: dict[str, float] = {
    "L01": 18, "L02": 8, "L03": 20, "L04": 22, "L05": 18, "L06": 12,
    "L07": 8, "L08": 18, "L09": 20, "L10": 14, "L11": 10, "L12": 8,
    "L13": 18, "L14": 18, "L15": 14, "L16": 8, "L17": 20, "L18": 16,
    "L19": 12, "L20": 8, "L21": 16, "L22": 14, "L23": 14, "L24": 14,
    "L25": 14, "L26": 8, "L27": 18, "L28": 12,
}

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
            "duration": DURATION[code],
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
