# D01 · 工程骨架与分层规范

> 截止：**11/20（今天）**　|　应交文件：1（本目录的 `01_工程结构说明.md`）　|　状态：✅ 已完成

## 这一项放什么

| 文件 | 说明 |
|---|---|
| `01_工程结构说明.md` | 主交付物：分层职责、包结构、依赖方向、五条红线、命名与配置规范、评审清单 |
| `00_README.md` | 本文件（说明放什么、验收标准） |

## 验收标准（对照 `00_交付总览.md`）

- [x] 有明确的四层划分：Controller / Service / Mapper / Entity&VO，且写清"谁能调谁"
- [x] 包结构落地成真实目录，不是纸上谈兵（见 `backend/src/main/java/com/uev/`）
- [x] 有命名规范、配置外部化规范、日志规范
- [x] 有可执行的评审清单（新人照着就能判断一个类写得对不对）
- [x] 骨架能编译、能跑（`mvn clean package` → BUILD SUCCESS，单测 7/7 通过）

## 支撑证据

- 代码：`backend/src/main/java/com/uev/`（63 个源文件编译通过）
- 分层实况：16 个 Controller 端点 → 6 个 Service → 5 个 Mapper → 14 张表 / 10 个视图
- 编译实测：`Tests run: 7, Failures: 0, Errors: 0` / `BUILD SUCCESS`
