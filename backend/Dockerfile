# ==============================================================================
# Dockerfile —— 后端镜像构建
#
# 维护人：D（杨姗姗）　|　骨架由 A（彭忠燕）提供，2026-11-19
#
# 多阶段构建：先 Maven 编译，再精简 JRE 运行镜像
# 镜像小、启动快，答辩现场拉取快
# ==============================================================================

# ---------- 阶段一：编译 ----------
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build

# 先只拷 pom.xml 做依赖预热（利用 Docker 层缓存，改代码不用重下依赖）
COPY pom.xml .
RUN mvn dependency:go-offline -B -q

# 再拷源码编译
COPY src ./src
RUN mvn clean package -DskipTests -B -q

# ---------- 阶段二：运行 ----------
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# 时区设为东八区，数据库时间才对得上
RUN apk add --no-cache tzdata curl && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

COPY --from=builder /build/target/uev-charge-analysis.jar app.jar

RUN mkdir -p /app/logs

EXPOSE 8080

ENV TZ=Asia/Shanghai \
    JAVA_OPTS="-Xms512m -Xmx1024m -Dfile.encoding=UTF-8"

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -sf http://localhost:8080/api/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
