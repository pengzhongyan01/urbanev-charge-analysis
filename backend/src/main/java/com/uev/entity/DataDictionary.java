package com.uev.entity;

import lombok.Data;

/**
 * data_dictionary 表实体 —— /api/dictionary（前端"数据源说明"页）。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class DataDictionary {
    private Long id;
    private String fileName;
    private String metricName;
    private String unit;
    private Long rowCount;
    private String grain;
    private String description;
}
