package com.uev;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.uev.common.ApiResponse;
import com.uev.common.ErrorCode;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

/**
 * 统一响应结构单测 —— D12「工程化五条」里"有单元测试"的证据。
 *
 * @author 杨姗姗（D 岗）
 */
class ApiResponseTest {

    private final ObjectMapper mapper = new ObjectMapper();

    @Test
    @DisplayName("ok() 的 code 必须是 200，message 必须是 success")
    void okShouldBeBusinessSuccess() {
        ApiResponse<String> resp = ApiResponse.ok("hello");
        assertEquals(200, resp.getCode());
        assertEquals("success", resp.getMessage());
        assertEquals("hello", resp.getData());
        assertNotNull(resp.getTimestamp());
    }

    @Test
    @DisplayName("fail() 不能带 data，且 message 与错误码一致")
    void failShouldCarryErrorCode() {
        ApiResponse<Void> resp = ApiResponse.fail(ErrorCode.PARAM_ERROR);
        assertEquals(400, resp.getCode());
        assertEquals(ErrorCode.PARAM_ERROR.getMessage(), resp.getMessage());
        assertNull(resp.getData());
    }

    @Test
    @DisplayName("序列化后的 JSON 必须包含 code/message/data/timestamp 四个字段")
    void jsonMustContainFourFields() throws Exception {
        String json = mapper.writeValueAsString(ApiResponse.ok(1));
        String parsed = json.replace("{", "").replace("}", "");
        assertEquals(4, parsed.split(",").length, "统一响应结构字段数应为 4，实际：" + json);
        assertNotNull(mapper.readTree(json).get("timestamp"));
    }
}
