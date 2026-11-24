package com.uev.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * sys_user 表实体（D03 设计的业务库表，D04 登录鉴权使用）。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class SysUser {
    @JsonIgnore
    private Long id;
    private String username;
    /** BCrypt 密文，任何情况下都不返回给前端 */
    @JsonIgnore
    private String passwordHash;
    private String realName;
    private String roleCode;
    /** 1 = 启用，0 = 停用 */
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;
}
