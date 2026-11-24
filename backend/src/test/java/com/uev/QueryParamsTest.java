package com.uev;

import com.uev.common.BusinessException;
import com.uev.common.QueryParams;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

/**
 * 公共查询参数单测 —— 重点是"缓存 key 必须包含全部筛选参数"这条契约。
 *
 * @author 杨姗姗（D 岗）
 */
class QueryParamsTest {

    @Test
    @DisplayName("同一组参数两次指纹必须相同（否则缓存永远命中不了）")
    void fingerprintStable() {
        QueryParams a = new QueryParams();
        a.setZoneId("308");
        a.setHourRange("17-19");
        QueryParams b = new QueryParams();
        b.setZoneId("308");
        b.setHourRange("17-19");
        assertEquals(a.fingerprint(), b.fingerprint());
    }

    @Test
    @DisplayName("改任何一个筛选条件，指纹都必须变（否则会拿到旧数据）")
    void fingerprintChangesWithFilter() {
        QueryParams a = new QueryParams();
        a.setZoneId("308");
        QueryParams b = new QueryParams();
        b.setZoneId("302");
        assertNotEquals(a.fingerprint(), b.fingerprint());

        QueryParams c = new QueryParams();
        c.setHourRange("17-19");
        QueryParams d = new QueryParams();
        d.setHourRange("0-6");
        assertNotEquals(c.fingerprint(), d.fingerprint());
    }

    @Test
    @DisplayName("startDate 晚于 endDate 属于参数错误，必须抛 400 而不是查库")
    void startAfterEndShouldFail() {
        QueryParams p = new QueryParams();
        p.setStartDate(LocalDate.of(2023, 2, 28));
        p.setEndDate(LocalDate.of(2022, 9, 1));
        BusinessException e = assertThrows(BusinessException.class, p::validate);
        assertEquals(400, e.getErrorCode().getCode());
    }

    @Test
    @DisplayName("hourRange 解析正确")
    void hourRangeParse() {
        QueryParams p = new QueryParams();
        p.setHourRange("17-19");
        assertEquals(17, p.hourFrom());
        assertEquals(19, p.hourTo());
    }
}
