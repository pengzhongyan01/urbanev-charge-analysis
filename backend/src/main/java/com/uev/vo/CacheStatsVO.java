package com.uev.vo;

import lombok.Data;

/**
 * /api/system/cache-stats 的 data 载荷 —— D07 缓存命中率与性能对比的取数接口。
 *
 * <p>答辩时直接打开这个接口截图：命中率、命中/未命中平均耗时，
 * 就是"加了缓存快了多少"的最硬证据。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class CacheStatsVO {
    /** redis / local —— 当前实际生效的缓存实现（降级后是 local） */
    private String type;
    private Long hitCount;
    private Long missCount;
    private Double hitRate;
    /** 命中缓存的平均耗时（毫秒） */
    private Double hitAvgMs;
    /** 未命中（走库）的平均耗时（毫秒） */
    private Double missAvgMs;
    /** 加速比 = missAvgMs / hitAvgMs */
    private Double speedup;
    /** 本地缓存条目数（redis 模式为 -1） */
    private Integer localEntries;
}
