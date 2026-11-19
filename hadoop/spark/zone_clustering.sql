-- =============================================================================
-- 创新点④ 分区聚类画像 · 特征表准备
-- =============================================================================
-- 维护人：姬婷婷（E 组）　|　协助：苏静（B 组）　|　交期：11/25（可选增量）
-- 骨架由 A（组长）提供，2026-11-19
--
-- 【为什么加这个】
--   老师给的高分思路图里，「数据分析」被标红且独立成一个环节，
--   说明分析深度是评分重点。
--   我们已有三个创新点都是「规则驱动 / 统计对比」，
--   聚类补上「数据驱动发现未知结构」这一维度：
--   不预设结论，让算法自己告诉我们 275 个分区有哪几类。
--
-- 【聚类要回答的业务问题】
--   275 个分区长得不一样。有的一直紧张、有的一直闲置、
--   有的 POI 密度高但桩还没跟上 —— 分几类？每类该什么运营策略？
--
-- 【执行顺序】
--   步骤1：建特征宽表（DWS 层）      ← 苏静做
--   步骤2：跑 KMeans（Spark MLlib）   ← 姬婷婷做
--   步骤3：解读簇特征 + 出图          ← 姬婷婷做
-- =============================================================================


-- =============================================================================
-- 步骤 1：构建聚类特征宽表
-- =============================================================================
-- 每个分区一行，7 个特征列
--
-- ★ 关键：KMeans 对量纲敏感。
--   桩密度(个/km²) 的数值量级可能是占用率的 1000 倍，
--   不做标准化的话，聚类结果会完全被桩密度主导 —— 这是最常见的坑。
-- =============================================================================

CREATE TABLE IF NOT EXISTS uev_dws.zone_cluster_features (
  zone_id           STRING  COMMENT '交通分区编号',
  avg_occupancy     DOUBLE  COMMENT '特征1 平均占用率 0-1',
  peak_valley_gap   DOUBLE  COMMENT '特征2 日内峰谷差',
  occupancy_std      DOUBLE  COMMENT '特征3 占用率标准差（波动率）',
  avg_duration      DOUBLE  COMMENT '特征4 平均充电时长（小时）',
  poi_density       DOUBLE  COMMENT '特征5 POI 密度（个/km²）',
  pile_density      DOUBLE  COMMENT '特征6 充电桩密度（个/km²）',
  price_std         DOUBLE  COMMENT '特征7 电价时序标准差（分时电价识别）'
)
COMMENT '分区聚类特征宽表（7 维特征，每行一分区）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

INSERT OVERWRITE TABLE uev_dws.zone_cluster_features
SELECT
    d.zone_id,
    d.avg_occupancy,
    d.peak_valley_gap,
    d.occupancy_std,
    d.avg_duration,
    -- POI 密度：个/km²（area 单位是 m²，换算要 ×1000000）
    di.poi_total / di.area * 1000000.0                AS poi_density,
    -- 桩密度：个/km²
    di.charge_count / di.area * 1000000.0             AS pile_density,
    di.price_std
FROM uev_dws.zone_day d
JOIN uev_dwd.dim_zone_info di ON d.zone_id = di.zone_id
GROUP BY d.zone_id, d.avg_occupancy, d.peak_valley_gap, d.occupancy_std,
         d.avg_duration, di.poi_total, di.area, di.charge_count, di.price_std;

-- 验证：应有 275 行，且各特征无 NULL
SELECT COUNT(*) AS total,
       SUM(CASE WHEN poi_density IS NULL THEN 1 ELSE 0 END) AS null_poi,
       SUM(CASE WHEN pile_density IS NULL THEN 1 ELSE 0 END) AS null_pile,
       ROUND(MIN(pile_density),2) AS min_pile_d,
       ROUND(MAX(pile_density),2) AS max_pile_d,
       ROUND(AVG(avg_occupancy),4) AS avg_occ
FROM uev_dws.zone_cluster_features;
-- 期望：total=275, null 全为 0
-- ★ 如果 pile_density 的 max/min 差了几百倍，说明标准化不是可选项而是必须做


-- =============================================================================
-- 步骤 2：KMeans 聚类（Spark MLlib）
-- =============================================================================
-- 完整可运行代码见同目录 ZoneClustering.scala
--
-- 三个必须在报告里写清楚的技术点：
--   ① 标准化（StandardScaler）：量纲差异会让聚类被单一特征主导
--   ② 固定随机种子 setSeed(42)：保证结果可复现 —— 这是加分点
--   ③ 肘部法选 k：画 k=2~6 的 WCSS 曲线说明为什么选 k=4
-- =============================================================================


-- =============================================================================
-- 步骤 3：解读聚类结果
-- =============================================================================
-- 3.1 落地表
CREATE TABLE IF NOT EXISTS uev_ads.zone_cluster (
  zone_id      STRING  COMMENT '交通分区编号',
  cluster_id   INT     COMMENT '簇编号 0-3',
  cluster_name STRING  COMMENT '簇名称（人工解读后命名）',
  avg_occupancy DOUBLE,
  peak_valley_gap DOUBLE,
  occupancy_std DOUBLE,
  avg_duration  DOUBLE,
  poi_density   DOUBLE,
  pile_density  DOUBLE,
  price_std     DOUBLE,
  longitude     DOUBLE,
  latitude      DOUBLE
)
COMMENT '分区聚类结果（含簇特征画像）'
STORED AS ORC
TBLPROPERTIES ('orc.compress'='SNAPPY');

-- 3.2 簇画像汇总（这是解读的主要依据）
--     这一张表的数字直接进报告 5.6 节
SELECT
    cluster_id,
    COUNT(*)                        AS zone_count,
    ROUND(AVG(avg_occupancy), 4)   AS avg_occ,
    ROUND(AVG(peak_valley_gap), 4) AS avg_gap,
    ROUND(AVG(occupancy_std), 4)   AS avg_std,
    ROUND(AVG(avg_duration), 3)    AS avg_dur,
    ROUND(AVG(poi_density), 1)     AS avg_poi_d,
    ROUND(AVG(pile_density), 1)     AS avg_pile_d,
    ROUND(AVG(price_std), 4)       AS avg_price_std
FROM uev_ads.zone_cluster
GROUP BY cluster_id
ORDER BY cluster_id;

-- 3.3 ★ 与供需失衡指数互相印证（这是本节最有说服力的一步）
--     预期：簇1（紧张型）的分区，平均失衡指数应该显著高于其他簇
--     如果不成立，说明聚类特征或失衡指数有一个算错了 —— 必须查清楚
SELECT
    c.cluster_name,
    COUNT(DISTINCT c.zone_id)                AS zone_count,
    ROUND(AVG(i.imbalance), 5)               AS avg_imbalance,
    ROUND(MAX(i.imbalance), 5)               AS max_imbalance,
    COUNT(DISTINCT CASE WHEN i.imbalance > 0 THEN c.zone_id END) AS shortage_zones
FROM uev_ads.zone_cluster c
JOIN uev_ads.imbalance_index i ON c.zone_id = i.zone_id
GROUP BY c.cluster_name
ORDER BY avg_imbalance DESC;

-- 3.4 命名建议（人工解读后回填 cluster_name）
--   簇A  avg_occ 高 + avg_gap 大 + avg_pile_d 低  →  '紧张型'
--   簇B  avg_occ 低 + avg_pile_d 高              →  '过剩型'
--   簇C  avg_occ 中 + avg_std 低                →  '稳定型'
--   簇D  avg_poi_d 高 + avg_pile_d 低            →  '潜力型'


-- =============================================================================
-- 步骤 4：与已有创新点联动的运营建议（可选加分）
-- =============================================================================
-- 把聚类结果和布点建议结合：
--   紧张型簇的分区 → 优先扩容
--   过剩型簇的分区 → 考虑迁移
--   潜力型簇的分区 → 提前布局
-- =============================================================================

SELECT
    c.cluster_name,
    COUNT(DISTINCT s.zone_id)              AS suggestion_count,
    SUM(s.suggested_piles)                 AS total_new_piles,
    ROUND(AVG(s.peak_gap), 5)              AS avg_peak_gap,
    GROUP_CONCAT(DISTINCT s.zone_id)       AS zone_list
FROM uev_ads.expansion_suggestion s
JOIN uev_ads.zone_cluster c ON s.zone_id = c.zone_id
GROUP BY c.cluster_name
ORDER BY suggestion_count DESC;


-- =============================================================================
-- 步骤 5：验收标准
-- =============================================================================
-- □ 特征表 275 行，无 NULL
-- □ KMeans 固定 seed=42，重复运行结果一致（报告里说明）
-- □ 四个簇的规模不极端（没有 270 个分区挤在一个簇里）
-- □ 3.3 的印证成立：紧张型的 avg_imbalance 显著最高
-- □ 地图图能画出来：275 个点按 4 种颜色着色
-- □ 报告 5.6 节写清：标准化、随机种子、肘部法选 k 三点
-- =============================================================================
