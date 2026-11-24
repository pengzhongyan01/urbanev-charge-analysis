package com.uev.auth;

import com.uev.common.BusinessException;
import com.uev.common.ErrorCode;
import com.uev.entity.SysUser;
import com.uev.mapper.SystemMapper;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

/**
 * 登录鉴权服务。
 *
 * <p>安全要点：
 * <ol>
 *   <li>用户名不存在与密码错误返回同一句"用户名或密码错误"，不泄露账号是否存在；</li>
 *   <li>密码用 BCrypt 校验，数据库里存的是密文（$2a$10$...），不是明文；</li>
 *   <li>停用账号（status=0）不允许登录。</li>
 * </ol>
 *
 * @author 杨珊珊（D 岗）
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final SystemMapper systemMapper;
    private final JwtUtil jwtUtil;
    private final BCryptPasswordEncoder passwordEncoder = new BCryptPasswordEncoder();

    public LoginResponse login(LoginRequest req) {
        SysUser user = systemMapper.selectUserByUsername(req.getUsername());
        if (user == null || !passwordEncoder.matches(req.getPassword(), user.getPasswordHash())) {
            log.warn("[登录失败] username={} 原因=用户名或密码错误", req.getUsername());
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "用户名或密码错误");
        }
        if (user.getStatus() == null || user.getStatus() != 1) {
            throw new BusinessException(ErrorCode.FORBIDDEN, "账号已停用，请联系管理员");
        }

        systemMapper.updateLastLogin(user.getId(), LocalDateTime.now());

        LoginResponse resp = new LoginResponse();
        resp.setToken(jwtUtil.generate(user.getUsername(), user.getRoleCode()));
        resp.setExpiresIn(jwtUtil.getExpireSeconds());
        resp.setUsername(user.getUsername());
        resp.setRealName(user.getRealName());
        resp.setRoleCode(user.getRoleCode());
        log.info("[登录成功] username={} role={}", user.getUsername(), user.getRoleCode());
        return resp;
    }

    /** /api/auth/me：解析令牌返回当前用户（不依赖鉴权开关，令牌无效一律 401） */
    public LoginResponse current(String authorization) {
        String token = extractToken(authorization);
        Claims claims = jwtUtil.parse(token);
        if (claims == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "令牌无效或已过期，请重新登录");
        }
        SysUser user = systemMapper.selectUserByUsername(claims.getSubject());
        if (user == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "用户不存在");
        }
        LoginResponse resp = new LoginResponse();
        resp.setUsername(user.getUsername());
        resp.setRealName(user.getRealName());
        resp.setRoleCode(user.getRoleCode());
        resp.setExpiresIn(claims.getExpiration().getTime() / 1000 - System.currentTimeMillis() / 1000);
        return resp;
    }

    public static String extractToken(String authorization) {
        if (authorization == null || authorization.isBlank()) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "未携带令牌，请先登录");
        }
        String token = authorization.trim();
        if (token.regionMatches(true, 0, "Bearer ", 0, 7)) {
            token = token.substring(7).trim();
        }
        if (token.isEmpty()) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED, "令牌为空");
        }
        return token;
    }
}
