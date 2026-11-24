package com.uev.mapper;

import com.uev.entity.ZoneOccupancy;
import com.uev.vo.HourlyVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 分区读接口。
 *
 * @author 杨姗姗（D 岗）
 */
@Mapper
public interface ZoneMapper {

    /** 分区占用率列表（热力图 / 地图），可按 zoneId 精确筛 */
    List<ZoneOccupancy> selectOccupancy(@Param("zoneId") String zoneId);

    /** 单个分区详情 */
    ZoneOccupancy selectByZoneId(@Param("zoneId") String zoneId);

    /** 单个分区的分区×小时画像（给详情页画峰谷曲线） */
    List<HourlyVO> selectZoneHourProfile(@Param("zoneId") String zoneId);
}
