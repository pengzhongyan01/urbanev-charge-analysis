package com.uev.auth;

import lombok.Data;

/**
 * 登录返回：令牌 + 有效期 + 最小必要的用户信息（不含密码）。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class LoginResponse {
    private String token;
    private String tokenType = "Bearer";
    private long expiresIn;
    private String username;
    private String realName;
    private String roleCode;
}
