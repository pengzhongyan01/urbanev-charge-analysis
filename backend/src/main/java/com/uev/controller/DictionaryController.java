package com.uev.controller;

import com.uev.common.ApiResponse;
import com.uev.entity.DataDictionary;
import com.uev.service.DictionaryService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * 数据字典接口（契约 03 · 2.11）。
 *
 * @author 杨姗姗（D 岗）
 */
@RestController
@RequestMapping("/api/dictionary")
@RequiredArgsConstructor
public class DictionaryController {

    private final DictionaryService dictionaryService;

    @GetMapping
    public ApiResponse<List<DataDictionary>> list() {
        return ApiResponse.ok(dictionaryService.list());
    }
}
