package com.uev.controller;

import com.uev.auth.AuthService;
import com.uev.auth.LoginRequest;
import com.uev.auth.LoginResponse;
import com.uev.common.ApiResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 登录鉴权接口（D04）。
 *
 * @author 杨珊珊（D 岗）
 */
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    /** 登录换令牌 */
    @PostMapping("/login")
    public ApiResponse<LoginResponse> login(@Valid @RequestBody LoginRequest req) {
        return ApiResponse.ok(authService.login(req));
    }

    /** 当前登录用户 */
    @GetMapping("/me")
    public ApiResponse<LoginResponse> me(
            @RequestHeader(value = "Authorization", required = false) String authorization) {
        return ApiResponse.ok(authService.current(authorization));
    }
}
