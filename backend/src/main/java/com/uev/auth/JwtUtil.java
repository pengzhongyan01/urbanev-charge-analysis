package com.uev.auth;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;

/**
 * JWT 工具 —— D04 登录鉴权的第二个交付物。
 *
 * <p>要点：
 * <ol>
 *   <li>密钥从 {@code uev.jwt.secret} 读，可被环境变量 JWT_SECRET 覆盖，<b>仓库里不落明文密钥</b>（对应参考作业"6 处明文密钥"的硬伤）；</li>
 *   <li>HS256 要求密钥长度 ≥ 256 bit（32 字节），启动时校验，不合格直接拒绝启动；</li>
 *   <li>令牌里只放 username 和 roleCode，不放任何敏感信息。</li>
 * </ol>
 *
 * @author 杨珊珊（D 岗）
 */
@Slf4j
@Component
public class JwtUtil {

    @Value("${uev.jwt.secret}")
    private String secret;

    @Value("${uev.jwt.expire-hours:8}")
    private long expireHours;

    private SecretKey key;

    @PostConstruct
    public void init() {
        byte[] bytes = secret.getBytes(StandardCharsets.UTF_8);
        if (bytes.length < 32) {
            throw new IllegalStateException("JWT 密钥长度不足 32 字节（HS256 要求 ≥256 bit），请检查 uev.jwt.secret");
        }
        this.key = Keys.hmacShaKeyFor(bytes);
        log.info("[鉴权] JWT 初始化完成，令牌有效期 {} 小时", expireHours);
    }

    public String generate(String username, String roleCode) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + expireHours * 3600_000L);
        return Jwts.builder()
                .subject(username)
                .claim("role", roleCode)
                .issuedAt(now)
                .expiration(expiry)
                .signWith(key)
                .compact();
    }

    /** 解析并校验；非法 / 过期返回 null（由调用方决定抛 401） */
    public Claims parse(String token) {
        try {
            return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
        } catch (Exception e) {
            log.debug("[鉴权] 令牌校验失败：{}", e.getMessage());
            return null;
        }
    }

    public long getExpireSeconds() {
        return expireHours * 3600L;
    }
}
