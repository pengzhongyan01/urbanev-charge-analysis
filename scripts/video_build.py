# -*- coding: utf-8 -*-
"""
合成最终演示视频 mp4
====================
流程：
  1. 读取 narration.json（镜头顺序 / 旁白 / 时长）
  2. 拼接画面帧 → 无声视频轨（按镜头时长）
  3. 拼接旁白 mp3 → 音频轨（段间插静音）
  4. 生成 SRT 字幕（按旁白文本切句 + 时间轴）
  5. ffmpeg 合成：视频 + 音频 + 烧录字幕 → 1080p H.264 mp4

运行：python scripts/video_build.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

ROOT = Path(r"D:/一系列作业/java后端/大作业/urbanev-charge-analysis")
TEMP = Path(os.environ.get("TEMP", r"C:/Users/彭忠燕/AppData/Local/Temp"))
FRAMES = TEMP / "uev_video_frames"
AUDIO = TEMP / "uev_video_audio"
WORK = TEMP / "uev_video_work"
OUTDIR = Path(r"D:/一系列作业/java后端/大作业/作业内容/彭忠燕/A09_提交包目录与命名/03.视频")
FINAL = OUTDIR / "第02组_城市充电桩数据分析系统_演示视频.mp4"

FF = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 30

# 镜头码 → 画面帧文件名
FRAMEMAP = {
    "L01": "L01_cover.jpg",
    "L02": "L02_sec_overview.jpg",
    "L03": "L03_arch.jpg",
    "L04": "L04_flow.jpg",
    "L05": "L05_sec_collect.jpg",
    "L06": "L06_flume.jpg",
    "L07": "L07_dw.jpg",
    "L08": "L08_table.jpg",
    "L09": "L09_code_dwd.jpg",
    "L10": "L10_sec_clean.jpg",
    "L11": "L11_code_long.jpg",
    "L12": "L12_code_range.jpg",
    "L13": "L13_code_dup.jpg",
    "L14": "L14_quality.jpg",
    "L15": "L15_sec_algo.jpg",
    "L16": "L16_formula.jpg",
    "L17": "L17_code_topn.jpg",
    "L18": "L18_imbalance.jpg",
    "L19": "L19_price.jpg",
    "L20": "L20_elastic.jpg",
    "L21": "L21_cluster.jpg",
    "L22": "L22_forecast.jpg",
    "L23": "L23_error.jpg",
    "L24": "L24_expansion.jpg",
    "L25": "L25_sec_backend.jpg",
    "L26": "L26_code_cache.jpg",
    "L27": "L27_code_key.jpg",
    "L28": "L28_apiarch.jpg",
    "L29": "L29_api.jpg",
    "L30": "L30_sec_demo.jpg",
    "L31": "L31_p1.jpg",
    "L32": "L32_p2.jpg",
    "L33": "L33_p3.jpg",
    "L34": "L34_p4.jpg",
    "L35": "L35_p5.jpg",
    "L36": "L36_p6.jpg",
    "L37": "L37_postman.jpg",
    "L38": "L38_sec_end.jpg",
    "L39": "L39_bullets.jpg",
    "L40": "L40_end.jpg",
}


def run(cmd: list[str], desc: str = "") -> None:
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(f"✗ {desc} 失败：\n{r.stderr[-2500:]}")
        sys.exit(1)
    print(f"  ✓ {desc}")


def srt_ts(t: float) -> str:
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def split_subtitle(text: str, dur: float) -> list[tuple[str, float]]:
    """按标点把旁白切成字幕句，返回 [(句, 该句时长)]。"""
    import re
    parts = re.split(r"(?<=[。！？；，、])", text)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        return [(text, dur)]
    # 按字数比例分配时长
    total_chars = sum(len(p) for p in parts)
    out = []
    acc = 0.0
    for i, p in enumerate(parts):
        if i == len(parts) - 1:
            d = dur - acc
        else:
            d = dur * len(p) / total_chars
            d = min(d, dur - acc - 0.15 * (len(parts) - i - 1))
        d = max(0.8, d)
        out.append((p, d))
        acc += d
    return out


def build_srt(manifest: list[dict]) -> Path:
    srt_path = WORK / "subtitles.srt"
    idx = 1
    t_cursor = 0.0
    lines = []
    for it in manifest:
        seg_dur = it["duration"]
        pieces = split_subtitle(it["text"], seg_dur - 0.3)
        t = t_cursor
        for txt, d in pieces:
            if len(txt) > 40:
                # 过长再切一次
                mid = len(txt) // 2
                cut = max(txt.rfind("，", 0, mid), txt.rfind("、", 0, mid), txt.rfind("；", 0, mid))
                if cut > 8:
                    sub = split_subtitle(txt[:cut + 1], d * (cut + 1) / len(txt))
                    for s2, d2 in sub:
                        lines.append(f"{idx}\n{srt_ts(t)} --> {srt_ts(t+d2)}\n{s2}\n")
                        idx += 1
                        t += d2
                    t2 = t
                    rest = txt[cut + 1:]
                    rest_pieces = split_subtitle(rest, d - (t - t_cursor))
                    for s2, d2 in rest_pieces:
                        lines.append(f"{idx}\n{srt_ts(t2)} --> {srt_ts(t2+d2)}\n{s2}\n")
                        idx += 1
                        t2 += d2
                    t = t2
                    continue
            lines.append(f"{idx}\n{srt_ts(t)} --> {srt_ts(t+d)}\n{txt}\n")
            idx += 1
            t += d
        t_cursor += seg_dur
    srt_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  ✓ 字幕 {idx-1} 条")
    return srt_path


def main() -> None:
    if WORK.exists():
        shutil.rmtree(WORK, ignore_errors=True)
    WORK.mkdir(parents=True, exist_ok=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads((AUDIO / "narration.json").read_text(encoding="utf-8"))
    print(f"镜头数 {len(manifest)}")

    # ── 1. 画面帧 → 静帧视频 ──────────────────────────────────────────
    print("\n[1/5] 拼接画面")
    # ★ 逐镜头先生成定长视频片段，再 concat。
    #   直接用 concat demuxer + JPEG + duration 指令不可靠：
    #   JPEG 是单帧图片，concat 的 duration 会被忽略，导致画面与旁白错位。
    seg_dir = WORK / "segs"
    seg_dir.mkdir(parents=True, exist_ok=True)
    seg_files = []
    for i, it in enumerate(manifest):
        code = it["code"]
        fp = FRAMES / FRAMEMAP[code]
        if not fp.exists():
            print(f"✗ 缺画面帧：{fp}")
            sys.exit(1)
        dur = it["duration"]
        seg = seg_dir / f"{code}.mp4"
        run([FF, "-y", "-hide_banner", "-loglevel", "error",
             "-loop", "1", "-framerate", str(FPS), "-t", f"{dur:.3f}",
             "-i", str(fp),
             "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
             "-pix_fmt", "yuv420p", str(seg)], f"片段 {code}")
        seg_files.append(seg)

    concat_file = WORK / "frames.txt"
    with concat_file.open("w", encoding="utf-8") as f:
        for seg in seg_files:
            f.write(f"file '{seg.as_posix()}'\n")

    silent_vid = WORK / "silent.mp4"
    run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(concat_file), "-c", "copy", str(silent_vid)], "静帧视频轨")

    # ── 2. 旁白 → 音频轨 ──────────────────────────────────────────────
    print("\n[2/5] 拼接旁白")
    # 先生成所有段间静音
    for i, it in enumerate(manifest):
        if i == len(manifest) - 1:
            break
        gap = it["duration"] - it["audio_duration"]
        sil = WORK / f"sil_{i}.wav"
        if gap > 0.05:
            run([FF, "-y", "-hide_banner", "-loglevel", "error",
                 "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                 "-t", f"{gap:.3f}", str(sil)], f"静音段 {i}")

    seg_list = WORK / "audio.txt"
    with seg_list.open("w", encoding="utf-8") as f:
        for i, it in enumerate(manifest):
            f.write(f"file '{Path(it['audio']).as_posix()}'\n")
            if i < len(manifest) - 1:
                sil = WORK / f"sil_{i}.wav"
                if sil.exists():
                    f.write(f"file '{sil.as_posix()}'\n")

    silent_a = WORK / "audio.m4a"
    run([FF, "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(seg_list), "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
         "-ac", "2", str(silent_a)], "旁白音轨")

    # ── 3. 字幕 ───────────────────────────────────────────────────────
    print("\n[3/5] 生成字幕")
    srt = build_srt(manifest)

    # ── 4. 合成 ───────────────────────────────────────────────────────
    print("\n[4/5] 烧录字幕并合成")
    # SRT 直接交给 subtitles 滤镜烧录（不作为独立输入流，避免 ASS 编码器问题）
    srt_escaped = srt.as_posix().replace("\\", "/").replace(":", r"\:").replace("'", r"\'")
    tmp_out = WORK / "final.mp4"
    run([FF, "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(silent_vid), "-i", str(silent_a),
         "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-level", "4.1",
         "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
         "-vf", f"subtitles='{srt_escaped}':force_style='FontName=Microsoft YaHei,"
                f"FontSize=17,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
                f"BorderStyle=3,Outline=1,Shadow=0,MarginV=14,Alignment=2'",
         "-movflags", "+faststart", str(tmp_out)], "最终合成")

    # ── 5. 交付 ───────────────────────────────────────────────────────
    print("\n[5/5] 输出到交付目录")
    shutil.copy2(tmp_out, FINAL)
    print(f"\n✓ {FINAL}")
    print(f"  体积 {FINAL.stat().st_size/1024/1024:.1f} MB")

    # 校验
    r = subprocess.run([FF, "-hide_banner", "-i", str(FINAL)], capture_output=True, text=True)
    for ln in r.stderr.splitlines():
        if "Duration:" in ln or "Video:" in ln or "Audio:" in ln:
            print("  " + ln.strip())


if __name__ == "__main__":
    main()
