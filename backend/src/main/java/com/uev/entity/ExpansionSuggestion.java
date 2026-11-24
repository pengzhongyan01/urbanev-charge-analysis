package com.uev.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

/**
 * expansion_suggestion 表实体 —— 创新点③ 布点扩容建议。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class ExpansionSuggestion {
    @JsonIgnore
    private Long id;
    private String zoneId;
    private Double longitude;
    private Double latitude;
    private Integer currentPiles;
    /** 建议新增桩数（不是总桩数，契约 03 特别强调） */
    private Integer suggestedPiles;
    /** 1 = 最高优先级 */
    private Integer priority;
    /** 完整中文句子，前端直接展示 */
    private String reason;
    private Double avgOccupancy;
    private Double peakGap;
}
