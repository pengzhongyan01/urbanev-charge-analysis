package com.uev.common;

import lombok.extern.slf4j.Slf4j;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import java.util.stream.Collectors;

/**
 * 全局异常处理 —— D02 交付物之一。
 *
 * <p>设计要点：
 * <ol>
 *   <li>业务异常（可预期）→ warn 级日志，不打堆栈，避免日志被刷爆；</li>
 *   <li>系统异常（不可预期）→ error 级日志 + 完整堆栈，便于排查；</li>
 *   <li>所有出口都转成 {@link ApiResponse}，前端永远拿到同一个结构；</li>
 *   <li><b>HTTP 状态码恒为 200，错误信息放在 body 的 code 里</b> ——
 *       这是契约 03 的约定："前端只判断 code === 200"。若返回 HTTP 500，
 *       前端 common.js 的 {@code if (!res.ok) throw} 会先抛异常，
 *       反而把后端写的中文提示丢掉，页面只剩 "HTTP 500"。</li>
 * </ol>
 *
 * @author 杨姗姗（D 岗）
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /** 业务异常：Service 主动抛出（参数错误、资源不存在、依赖不可用…） */
    @ExceptionHandler(BusinessException.class)
    public ApiResponse<Void> handleBusiness(BusinessException e) {
        log.warn("[业务异常] code={} message={}", e.getErrorCode().getCode(), e.getMessage());
        return ApiResponse.fail(e.getErrorCode(), e.getMessage());
    }

    /** @RequestBody 上的 @Valid 校验失败 */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ApiResponse<Void> handleValid(MethodArgumentNotValidException e) {
        String detail = e.getBindingResult().getFieldErrors().stream()
                .map(this::formatFieldError)
                .collect(Collectors.joining("; "));
        log.warn("[参数校验失败] {}", detail);
        return ApiResponse.fail(ErrorCode.PARAM_ERROR, detail);
    }

    /** 查询对象（POJO）绑定校验失败 */
    @ExceptionHandler(BindException.class)
    public ApiResponse<Void> handleBind(BindException e) {
        String detail = e.getBindingResult().getFieldErrors().stream()
                .map(this::formatFieldError)
                .collect(Collectors.joining("; "));
        return ApiResponse.fail(ErrorCode.PARAM_ERROR, detail);
    }

    /** @RequestParam 上的约束注解（@Pattern / @Min 等）校验失败 */
    @ExceptionHandler(ConstraintViolationException.class)
    public ApiResponse<Void> handleConstraint(ConstraintViolationException e) {
        String detail = e.getConstraintViolations().stream()
                .map(this::formatViolation)
                .collect(Collectors.joining("; "));
        return ApiResponse.fail(ErrorCode.PARAM_ERROR, detail);
    }

    /** 必填查询参数缺失，例如 /charts/imbalance 少了 limit */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ApiResponse<Void> handleMissingParam(MissingServletRequestParameterException e) {
        return ApiResponse.fail(ErrorCode.PARAM_ERROR, "缺少必填参数：" + e.getParameterName());
    }

    /** 参数类型不匹配，例如 zoneId=abc 但要求数字 */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ApiResponse<Void> handleTypeMismatch(MethodArgumentTypeMismatchException e) {
        return ApiResponse.fail(ErrorCode.PARAM_ERROR,
                "参数 " + e.getName() + " 类型不正确，期望 " + e.getRequiredType());
    }

    /** 请求体不是合法 JSON */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ApiResponse<Void> handleUnreadable(HttpMessageNotReadableException e) {
        return ApiResponse.fail(ErrorCode.PARAM_ERROR, "请求体格式错误，需为合法 JSON");
    }

    /** 方法不支持，例如对只读接口发 POST */
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public ApiResponse<Void> handleMethod(HttpRequestMethodNotSupportedException e) {
        return ApiResponse.fail(ErrorCode.METHOD_NOT_ALLOWED, e.getMessage());
    }

    /**
     * 数据访问异常 —— MySQL 挂了 / 连接池打满 / SQL 写错了。
     *
     * <p>不能落到兜底的 500"服务器内部错误"：那样前端和用户都不知道是数据库的问题。
     * 这里统一转成 503 + 人话，同时在日志里留完整堆栈给后端排查。
     */
    @ExceptionHandler(org.springframework.dao.DataAccessException.class)
    public ApiResponse<Void> handleDataAccess(org.springframework.dao.DataAccessException e) {
        log.error("[数据访问异常] 数据库不可用或 SQL 执行失败", e);
        return ApiResponse.fail(ErrorCode.DB_UNAVAILABLE);
    }

    /** 兜底：任何没被上面接住的异常 */
    @ExceptionHandler(Exception.class)
    public ApiResponse<Void> handleAll(Exception e) {
        // Spring 6 把「路径不存在」抛成 NoResourceFoundException，必须单独转 404，
        // 否则前端拼错一个接口名会看到 500，误以为是后端崩了
        if (e.getClass().getName().contains("NoResourceFoundException")
                || e instanceof org.springframework.web.servlet.resource.NoResourceFoundException) {
            log.warn("[路径不存在] {}", e.getMessage());
            return ApiResponse.fail(ErrorCode.NOT_FOUND, "接口不存在，请核对路径");
        }
        log.error("[系统异常] 未预期异常，已统一转为 500 响应", e);
        return ApiResponse.fail(ErrorCode.SERVICE_ERROR);
    }

    private String formatFieldError(FieldError fe) {
        return fe.getField() + " " + fe.getDefaultMessage();
    }

    private String formatViolation(ConstraintViolation<?> cv) {
        String path = cv.getPropertyPath().toString();
        int idx = path.lastIndexOf('.');
        String field = idx >= 0 ? path.substring(idx + 1) : path;
        return field + " " + cv.getMessage();
    }
}
