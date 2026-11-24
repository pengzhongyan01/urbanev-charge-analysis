package com.uev.vo;

import lombok.Data;

import java.util.List;

/**
 * /api/charts/imbalance 的 data 载荷：{ "top": [ ... ] }。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class ImbalanceTopVO {
    private List<com.uev.entity.ImbalanceIndex> top;
}
