package com.uev.vo;

import com.uev.entity.ZoneOccupancy;
import lombok.Data;

import java.util.List;

/**
 * /api/zones/{zoneId} 的 data 载荷 —— 分区详情 + 该分区的峰谷时段。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class ZoneDetailVO {
    private ZoneOccupancy zone;
    /** 该分区占用率最高的 5 个时段 */
    private List<HourlyVO> peakHours;
}
