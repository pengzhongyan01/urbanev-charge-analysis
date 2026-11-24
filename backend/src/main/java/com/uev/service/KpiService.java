package com.uev.service;

import com.uev.aspect.UevCache;
import com.uev.common.BusinessException;
import com.uev.common.QueryParams;
import com.uev.entity.DashboardKpi;
import com.uev.mapper.KpiMapper;
import com.uev.vo.KpiVO;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;

/**
 * KPI 概览服务。
 *
 * @author 杨姗姗（D 岗）
 */
@Service
@RequiredArgsConstructor
public class KpiService {

    private final KpiMapper kpiMapper;

    /** 契约 03 · 2.2，缓存 300 秒（契约 1.4） */
    @UevCache(prefix = "uev:kpi", ttl = 300)
    public KpiVO getKpi(QueryParams params) {
        params.validate();
        DashboardKpi kpi = kpiMapper.selectLatest();
        if (kpi == null) {
            // 表里没数据不代表系统坏了：明确告诉前端"数据未就绪"，比返回 500 更友好
            throw BusinessException.notFound("KPI 数据尚未就绪（ADS 层可能还没导出），请联系 B 岗");
        }
        KpiVO vo = new KpiVO();
        BeanUtils.copyProperties(kpi, vo);
        vo.setRegions(kpiMapper.selectRegions());
        return vo;
    }
}
