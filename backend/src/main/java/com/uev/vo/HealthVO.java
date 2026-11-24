package com.uev.vo;

import lombok.Data;

import java.util.Map;

/**
 * /api/health 的 data 载荷 —— 启动脚本判就绪、冒烟测试体检、前端右上角状态灯。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class HealthVO {
    /** UP / DEGRADED / DOWN */
    private String status;
    private String timestamp;
    private String application;
    private String version;
    /** 必须来自配置 uev.data.region-count，默认 275（不是 96） */
    private Integer regionCount;
    /** components.mysql / components.redis */
    private Map<String, String> components;
}
