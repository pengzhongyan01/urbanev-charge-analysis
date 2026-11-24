package com.uev.service;

import com.uev.aspect.UevCache;
import com.uev.common.BusinessException;
import com.uev.common.QueryParams;
import com.uev.entity.ZoneOccupancy;
import com.uev.mapper.ZoneMapper;
import com.uev.vo.HourlyVO;
import com.uev.vo.ZoneDetailVO;
import com.uev.vo.ZoneListVO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 分区服务：地图散点、分区清单、分区详情。
 *
 * @author 杨姗姗（D 岗）
 */
@Service
@RequiredArgsConstructor
public class ZoneService {

    private final ZoneMapper zoneMapper;

    /** 分区清单（下拉框 / 表格页），不缓存：数据量小且要实时 */
    public ZoneListVO listZones(String keyword) {
        List<ZoneOccupancy> zones = zoneMapper.selectOccupancy(null);
        if (keyword != null && !keyword.isBlank()) {
            String kw = keyword.trim();
            zones = zones.stream()
                    .filter(z -> z.getZoneId() != null && z.getZoneId().contains(kw))
                    .toList();
        }
        return ZoneListVO.of(zones);
    }

    /** 契约 03 · 2.3 热力图，缓存 600 秒（契约 1.4） */
    @UevCache(prefix = "uev:zone_occ", ttl = 600)
    public List<ZoneOccupancy> getOccupancy(QueryParams params) {
        params.validate();
        return zoneMapper.selectOccupancy(params.getZoneId());
    }

    /** 分区详情：基础画像 + 峰值时段 TOP5 */
    public ZoneDetailVO getDetail(String zoneId) {
        if (zoneId == null || zoneId.isBlank()) {
            throw BusinessException.paramError("zoneId 不能为空");
        }
        ZoneOccupancy zone = zoneMapper.selectByZoneId(zoneId);
        if (zone == null) {
            throw BusinessException.notFound("分区 " + zoneId + " 不存在");
        }
        List<HourlyVO> peaks = zoneMapper.selectZoneHourProfile(zoneId);
        ZoneDetailVO vo = new ZoneDetailVO();
        vo.setZone(zone);
        vo.setPeakHours(peaks);
        return vo;
    }
}
