package com.uev.mapper;

import com.uev.entity.DataDictionary;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 数据字典读接口。
 *
 * @author 杨姗姗（D 岗）
 */
@Mapper
public interface DictionaryMapper {

    List<DataDictionary> selectAll();
}
