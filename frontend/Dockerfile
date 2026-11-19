# ==============================================================================
# Dockerfile —— 前端 Nginx 镜像
#
# 维护人：C（贺欢欢）　|　骨架由 A（组长）提供，2026-11-19
# ==============================================================================

FROM nginx:1.25-alpine

# 复制静态文件
COPY . /usr/share/nginx/html/

# 替换默认配置，加入后端反向代理
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
