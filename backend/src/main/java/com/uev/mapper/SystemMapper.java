package com.uev.mapper;

import com.uev.entity.QueryLog;
import com.uev.entity.SysUser;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;

/**
 * 系统表读接口（用户 + 查询日志）。
 *
 * @author 杨姗姗（D 岗）
 */
@Mapper
public interface SystemMapper {

    SysUser selectUserByUsername(@Param("username") String username);

    int updateLastLogin(@Param("id") Long id, @Param("lastLoginAt") LocalDateTime lastLoginAt);

    int insertQueryLog(QueryLog log);
}
