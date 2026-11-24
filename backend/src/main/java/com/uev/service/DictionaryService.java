package com.uev.service;

import com.uev.entity.DataDictionary;
import com.uev.mapper.DictionaryMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * 数据字典服务 —— 前端"数据源说明"页。
 *
 * @author 杨珊珊（D 岗）
 */
@Service
@RequiredArgsConstructor
public class DictionaryService {

    private final DictionaryMapper dictionaryMapper;

    public List<DataDictionary> list() {
        // 字典表空着也返回空数组，不抛异常：前端页面能正常渲染"暂无数据"
        return dictionaryMapper.selectAll();
    }
}
