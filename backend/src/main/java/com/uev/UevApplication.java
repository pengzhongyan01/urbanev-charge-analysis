package com.uev;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.core.env.Environment;

/**
 * UrbanEV 后端启动类。
 *
 * <p>分层约定（D01 分层规范）：
 * Controller（只做参数接收与响应包装） → Service（业务编排 / 缓存 / 降级）
 * → Mapper（SQL，只读 ADS 表与视图） → MySQL。
 *
 * @author 杨珊珊（D 岗）
 */
@SpringBootApplication
@MapperScan("com.uev.mapper")
public class UevApplication {

    public static void main(String[] args) {
        Environment env = SpringApplication.run(UevApplication.class, args).getEnvironment();
        String port = env.getProperty("server.port", "8080");
        System.out.println("========================================================");
        System.out.println(" UrbanEV 后端启动成功");
        System.out.println(" 本机访问   : http://localhost:" + port + "/api/health");
        System.out.println(" 缓存模式   : " + env.getProperty("uev.cache.type", "auto"));
        System.out.println(" 鉴权开关   : " + env.getProperty("uev.auth.enabled", "false"));
        System.out.println("========================================================");
    }
}
