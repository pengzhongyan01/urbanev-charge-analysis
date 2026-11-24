package com.uev.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 分区下拉框的一项：{ zoneId, pileCount }。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegionVO {
    private String zoneId;
    private Integer pileCount;
}
