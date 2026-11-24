package com.uev.mapper;

import com.uev.entity.DashboardKpi;
import com.uev.vo.RegionVO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * KPI 读接口 —— 只读视图 v_kpi_overview（D08 交付物：接入 MySQL 视图）。
 *
 * @author 杨姗姗（D 岗）
 */
@Mapper
public interface KpiMapper {

    /** 取最新一条 KPI 快照 */
    DashboardKpi selectLatest();

    /** 分区下拉框数据：{ zoneId, pileCount } */
    List<RegionVO> selectRegions();
}
