# E 组·分析与模型脚本（analysis/）

> 维护人：姬婷婷（E 岗）　|　口径依据：`docs/contracts/02-指标定义表.md` v1.2
> 覆盖交付项：E01 探索性分析、E02 σ 可分性、E04—E09 四创新点与布点、E10 模型持久化、E13 第五章

---

## 一、这两个脚本干什么

| 脚本 | 作用 | 产物 |
|---|---|---|
| `01_analysis.py` | 读 UrbanEV 原始宽表，算 12 项基础指标 + 4 个创新点，出落地表 CSV、9 张图表、结论 JSON、模型文件 | `analysis/output/` |
| `02_build_docx.py` | 把 `docs/report/第五章_姬婷婷.md` 排版成 Word（宋体小四、首行缩进 2 字符、三线表、图注在图下） | `analysis/output/第五章_姬婷婷.docx` |

**两份产物都不进 Git**（`analysis/output/` 已列入 .gitignore），需要原始文件时自己跑一遍。

## 二、环境

```
Python 3.10+
pandas numpy scikit-learn scipy matplotlib python-docx joblib
```

Windows 下命令是 `python`（不是 `python3`）。

## 三、数据

需要 9 个 UrbanEV 原始 CSV：`occupancy.csv`、`duration.csv`、`volume.csv`、`volume-11kW.csv`、
`e_price.csv`、`s_price.csv`、`inf.csv`、`poi.csv`、`weather_central.csv`。

脚本按以下顺序自动探测（与 `scripts/find_data.sh` 同口径，**不需要改代码**）：

1. 环境变量 `UEV_DATA_DIR`
2. 仓库内 `data/raw/`
3. 仓库同级 `../数据/UrbanEV/`
4. 上层 `../../数据/UrbanEV/`

一条命令准备好：`bash scripts/download_data.sh`。

## 四、怎么跑

```bash
python analysis/01_analysis.py     # 约 1—2 分钟，确定性：重跑数字不变
python analysis/02_build_docx.py   # 需要本机装 Word 才导出 PDF 预览
```

中途会打印 `[数据] <路径>` 与 `[来源] 真实 UrbanEV 数据 / 样例合成数据`，先确认这一行没读到合成数据。

## 五、口径不能改的地方

| 项 | 固定值 | 依据 |
|---|---|---|
| 失衡指数 | `I = 需求份额 − 运力份额`，份额按 volume 与 charge_count | 契约创新点① |
| TOU 阈值 | `σ_price > 0.05` | 契约创新点② |
| 弹性定义 | 高峰 17—19 时均值 − 低谷 0—6 时均值 | 契约创新点② |
| 预测 | 同星期同小时均值 × γ（近 7 天/全期） | 契约创新点③ |
| 训练/验证切分 | 前 174 天训练，最后 7 天（02-22~02-28）验证 | 契约创新点③ |
| 布点系数 | `CEIL(峰值失衡 × 现有桩数 × 0.3)`，按峰值失衡降序 | 契约创新点③ |
| 聚类 | 7 维特征、k=4、种子 42、肘部法 k=2~6 | 契约创新点④ |

改了上面任何一条，下游 B（DWS/ADS）、D（接口返回）、C（图表）都要跟着返工——**要走契约 PR，不能直接改脚本**。

## 六、已知的实测差异（不是 bug，是数据事实）

1. **分区编号里没有 308 / 302**。契约验收举例的“南山 308、福田 302”在本数据集 275 个分区中不存在，脚本改用“TOP10 中是否多数同时位列电量前十”做等价校验。
2. **分区级 MAPE 到不了 15%**。主方案 76.94%，按契约兜底后 74.01%；全市逐小时 5.31%、日聚合 WAPE 1.31% 可用。报告按“全市 / 分区日聚合 / 分区逐小时”三层如实表述。
3. **M6 是分区小时累计时长**，不是单次充电时长（单桩折算后与 M1 的 0.1574 小时/桩·时一致，两指标互校）。
4. **M9 按最近分区质心落区**，属近似；B 组若用 MapReduce 做精确空间连接，数值会有小幅差异。
