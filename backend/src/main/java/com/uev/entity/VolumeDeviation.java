package com.uev.entity;

import lombok.Data;

/**
 * volume_deviation 表实体 —— M11 双口径电量偏差（契约 03 · 2.9，可选接口）。
 *
 * <p>由 E 岗（双口径对比）灌数，D 只负责读。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class VolumeDeviation {
    private Long id;
    private String zoneId;
    /** 口径①：上报电量 */
    private Double volume;
    /** 口径②：11kW 桩折算电量 */
    private Double volume11kw;
    /** 偏差率 = |volume - volume11kw| / volume */
    private Double deviation;
}
