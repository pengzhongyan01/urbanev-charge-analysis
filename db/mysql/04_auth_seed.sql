-- =============================================================================
-- 04_auth_seed.sql —— 用户与角色初始化（D04 交付配套）
-- =============================================================================
-- 维护人：杨姗姗（D 岗）
-- 说明：演示账号 admin / uev123456 与 analyst / uev123456
--       密码字段存 BCrypt 密文（$2a$10$... 固定 60 字符），不放明文。
--       明文只出现在本文档注释与本机演示说明里，不进代码仓库。
-- =============================================================================

USE uev_charge;

INSERT INTO sys_role (role_code, role_name, description) VALUES
 ('ADMIN',   '管理员',  '全部接口 + 缓存管理'),
 ('ANALYST', '分析员',  '全部查询接口，无系统管理权限'),
 ('VIEWER',  '访客',    '仅首页与图表查询')
ON DUPLICATE KEY UPDATE role_name = VALUES(role_name);

-- BCrypt('uev123456', cost=10)
INSERT INTO sys_user (username, password_hash, real_name, role_code, status) VALUES
 ('admin',   '$2a$10$AizSB.CVvR9Y0agOlJjXbeTzWi3CjUt4D3OA.TlDq4fqyMpVyWiJK', '杨姗姗', 'ADMIN',  1),
 ('analyst', '$2a$10$AizSB.CVvR9Y0agOlJjXbeTzWi3CjUt4D3OA.TlDq4fqyMpVyWiJK', '分析账号', 'ANALYST', 1)
ON DUPLICATE KEY UPDATE password_hash = VALUES(password_hash), status = VALUES(status);

-- 校验：应返回 2 行，且 password_hash 全部以 $2a$ 开头
SELECT username, role_code, status, LEFT(password_hash, 7) AS hash_prefix FROM sys_user;
