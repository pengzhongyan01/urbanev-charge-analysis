package com.uev.common;

import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;
import java.util.Objects;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * 公共查询参数 —— 契约 03 · 1.3 节。
 *
 * <p>所有图表接口都支持这 5 个可选参数；<b>缓存 key 必须包含全部筛选参数</b>，
 * 否则改了筛选条件会拿到旧数据（契约里点名的"最常见的缓存 bug"）。
 *
 * @author 杨姗姗（D 岗）
 */
@Data
public class QueryParams {

    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate startDate;

    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate endDate;

    /** 时段：0-6 / 7-9 / 10-16 / 17-19 / 20-23 */
    @Pattern(regexp = "^([0-9]|1[0-9]|2[0-3])-([0-9]|1[0-9]|2[0-3])$", message = "需形如 17-19")
    private String hourRange;

    /** 分区编号，空表示全部 */
    @Size(max = 20, message = "长度不能超过 20")
    private String zoneId;

    /** TOU / FLAT，空表示全部 */
    @Pattern(regexp = "^(TOU|FLAT)?$", message = "只能是 TOU 或 FLAT")
    private String priceType;

    @Min(value = 1, message = "最小值为 1")
    @Max(value = 100, message = "最大值为 100")
    private Integer limit;

    /** 解析 hourRange 的起始小时；无值返回 null */
    public Integer hourFrom() {
        if (hourRange == null || hourRange.isBlank()) {
            return null;
        }
        return Integer.parseInt(hourRange.split("-")[0]);
    }

    /** 解析 hourRange 的结束小时（含） */
    public Integer hourTo() {
        if (hourRange == null || hourRange.isBlank()) {
            return null;
        }
        return Integer.parseInt(hourRange.split("-")[1]);
    }

    public void validate() {
        if (startDate != null && endDate != null && startDate.isAfter(endDate)) {
            throw BusinessException.paramError("startDate 不能晚于 endDate");
        }
        Integer from = hourFrom();
        Integer to = hourTo();
        if (from != null && to != null && from > to) {
            throw BusinessException.paramError("hourRange 起始小时不能大于结束小时");
        }
    }

    /**
     * 稳定的参数指纹，用于拼缓存 key。
     * 注意：这里把 null 与空串统一成 "-"，保证"没传"和"传了空"命中同一个 key。
     */
    public String fingerprint() {
        return "s=" + Objects.toString(startDate, "-")
                + "&e=" + Objects.toString(endDate, "-")
                + "&h=" + Objects.toString(hourRange, "-")
                + "&z=" + Objects.toString(zoneId, "-")
                + "&p=" + Objects.toString(priceType, "-")
                + "&l=" + Objects.toString(limit, "-");
    }
}
