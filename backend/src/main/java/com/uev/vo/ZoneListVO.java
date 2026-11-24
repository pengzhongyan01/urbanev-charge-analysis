package com.uev.vo;

import com.uev.entity.ZoneOccupancy;
import lombok.Data;

import java.util.List;

/**
 * /api/zones 的 data 载荷 —— 分区下拉框 / 分区清单。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class ZoneListVO {
    private Integer total;
    private List<ZoneOccupancy> zones;

    public static ZoneListVO of(List<ZoneOccupancy> zones) {
        ZoneListVO vo = new ZoneListVO();
        vo.setZones(zones);
        vo.setTotal(zones == null ? 0 : zones.size());
        return vo;
    }
}
