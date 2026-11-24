package com.uev.config;

import com.uev.auth.AuthService;
import com.uev.auth.JwtUtil;
import com.uev.common.BusinessException;
import com.uev.common.ErrorCode;
import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * 鉴权拦截器 —— D04 交付物之一。
 *
 * <p>{@code uev.auth.enabled=false}（默认）时直接放行，保证前端骨架裸 GET 也能联调；
 * 打开开关后，除 /api/health 与 /api/auth/login 外都要求带 {@code Authorization: Bearer <token>}。
 *
 * @author 杨珊珊（D 岗）
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AuthInterceptor implements HandlerInterceptor {

    public static final String ATTR_USERNAME = "uev.username";
    public static final String ATTR_ROLE = "uev.role";

    private final JwtUtil jwtUtil;

    @Value("${uev.auth.enabled:false}")
    private boolean enabled;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        if (!enabled) {
            return true;
        }
        // CORS 预检请求没有 Authorization 头，必须放行，否则浏览器直接报跨域错误
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        String token = AuthService.extractToken(request.getHeader("Authorization"));
        Claims claims = jwtUtil.parse(token);
        if (claims == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "令牌无效或已过期，请重新登录");
        }
        request.setAttribute(ATTR_USERNAME, claims.getSubject());
        request.setAttribute(ATTR_ROLE, claims.get("role"));
        return true;
    }
}
