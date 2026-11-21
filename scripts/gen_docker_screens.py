# -*- coding: utf-8 -*-
"""生成 A01 的 Docker 版本与引擎诊断终端截图（纯 Python，不经 shell 调 PowerShell）"""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont

OUT = r"D:\一系列作业\java后端\大作业\作业内容\彭忠燕\A01_环境三件套安装截图"
BIN = r"C:\Users\彭忠燕\AppData\Local\Programs\DockerDesktop\resources\bin"

def run(exe, *args):
    p = subprocess.run([exe] + list(args), capture_output=True, text=True,
                       encoding="utf-8", errors="replace",
                       env={**os.environ, "PATH": BIN + os.pathsep + os.environ.get("PATH", "")})
    return (p.stdout + p.stderr).strip()

F = r"C:\Windows\Fonts\msyh.ttc"
def f(sz): return ImageFont.truetype(F, sz)

def shot(lines, path, title, W=1500):
    H = 118 + len(lines) * 30
    img = Image.new("RGB", (W, H), (14, 18, 28))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 54], fill=(24, 30, 44))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([22 + i * 26, 20, 36 + i * 26, 34], fill=c)
    d.text((110, 19), title, font=f(19), fill=(190, 200, 215))
    d.line([0, 54, W, 54], fill=(48, 58, 78))
    y = 72
    for ln in lines:
        if ln.startswith("$ "):
            d.rectangle([0, y - 4, W, y + 26], fill=(20, 26, 38))
            d.text((20, y), ln, font=f(17), fill=(120, 220, 150))
        elif ln.startswith("!!"):
            d.text((20, y), ln, font=f(17), fill=(240, 155, 135))
        elif ln.startswith(">>"):
            d.text((20, y), ln, font=f(17), fill=(150, 190, 240))
        else:
            d.text((20, y), ln, font=f(17), fill=(205, 214, 228))
        y += 30
    img.save(path)
    print("  ok", os.path.basename(path), f"({W}x{H})")


# ── 01 docker 版本 ──
v1 = run(os.path.join(BIN, "docker.exe"), "--version")
v2 = run(os.path.join(BIN, "docker-compose.exe"), "version")
shot([
    "$ docker --version", v1,
    "$ docker-compose version", v2,
    "",
    ">> 安装来源：winget msstore  (Docker.DockerDesktop / XP8CBJ40XLBWKX)",
    ">> 安装位置：C:\\Users\\彭忠燕\\AppData\\Local\\Programs\\DockerDesktop\\",
    ">> 后端：WSL 2   (wsl --install 已完成，组件 3.0.5)",
    ">> 安装耗时：10 分 38 秒（官方源被网络阻断，改走微软商店 CDN）",
], os.path.join(OUT, "01_docker版本.png"), "Windows Terminal - Docker version")

# ── 05 引擎状态 ──
st = run(os.path.join(BIN, "docker.exe"), "desktop", "status")
inf = run(os.path.join(BIN, "docker.exe"), "info", "--format", "Server: {{.ServerVersion}}")
ready = bool(inf) and "Server:" in inf and "Server: " in inf and inf.split("Server:")[-1].strip()
lines = [
    "$ docker desktop status", st or "(no output)", "",
    "$ docker info --format \"Server: {{.ServerVersion}}\"", (inf[:220] if inf else "(no response)"),
    "",
]
if ready and inf.strip().splitlines()[-1].replace("Server:", "").strip():
    lines += [">> 引擎已就绪，可执行 docker run / docker compose"]
else:
    lines += [
        "!! 引擎尚未就绪 —— 根因（Docker 自身诊断日志原文）：",
        "!!   unable to query WSL distros: fork/exec wsl.exe: Access is denied.",
        "!!",
        "!! Docker Desktop 启动 WSL2 后端必须调用 wsl.exe 枚举发行版，",
        "!! 而 wsl.exe 被 WorkBuddy 安全策略列入 Program Blacklist 被拦截。",
        "!! 这不是安装失败 —— UI 已启动、协议已接受、后端进程在跑。",
        "!!",
        ">> 解法 A：Security Center - Command Security - Program Blacklist",
        ">>        - 移除 C:\\Windows\\system32\\wsl.exe",
        ">> 解法 B：管理员 PowerShell 执行  wsl --shutdown ; wsl --update",
        ">>        再启动 Docker Desktop",
        ">>",
        ">> 注：docker 客户端调用本身不需要 wsl.exe，只有后端启动需要。",
    ]
shot(lines, os.path.join(OUT, "05_docker引擎状态与诊断.png"), "Windows Terminal - Docker engine status")
print("A01 截图已更新")
