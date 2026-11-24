package com.uev.config;

import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * MVC 配置：拦截器 + 跨域。
 *
 * <p>拦截器顺序很重要：先鉴权（AuthInterceptor）再记日志（QueryLogInterceptor），
 * 这样未通过鉴权的请求不会污染 query_log。
 *
 * @author 杨珊珊（D 岗）
 */
@Configuration
@RequiredArgsConstructor
public class WebConfig implements WebMvcConfigurer {

    private final AuthInterceptor authInterceptor;
    private final QueryLogInterceptor queryLogInterceptor;

    @Value("${uev.cors.allowed-origins:*}")
    private String allowedOrigins;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(authInterceptor)
                .addPathPatterns("/api/**")
                .excludePathPatterns("/api/health", "/api/auth/login", "/error")
                .order(1);
        registry.addInterceptor(queryLogInterceptor)
                .addPathPatterns("/api/**")
                .order(2);
    }

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOriginPatterns(allowedOrigins.split(","))
                .allowedMethods("GET", "POST", "OPTIONS")
                .allowedHeaders("*")
                .maxAge(3600);
    }
}
