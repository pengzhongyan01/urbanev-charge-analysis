package com.uev.entity;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * query_log 表实体 —— 接口查询日志，答辩时展示"系统可审计"。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class QueryLog {
    private Long id;
    private String apiPath;
    private String params;
    private Integer costMs;
    /** 1 = 命中缓存，0 = 回源查库 */
    private Integer hitCache;
    private LocalDateTime createdAt;
}
