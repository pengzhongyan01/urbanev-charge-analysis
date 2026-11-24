package com.uev.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

/**
 * imbalance_index 表实体 —— 创新点① 供需失衡指数 TOP。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class ImbalanceIndex {
    @JsonIgnore
    private Long id;
    private String zoneId;
    private Double longitude;
    private Double latitude;
    private Integer hourOfDay;
    private Double demandShare;
    private Double supplyShare;
    /** I(z,t)，正值 = 供不应求 */
    private Double imbalance;
    private Integer rankNo;
}
