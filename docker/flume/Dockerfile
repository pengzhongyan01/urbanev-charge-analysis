# ==============================================================================
# Flume 采集镜像 —— 基于 apache/hadoop:3.3.6 再装 Flume 1.11.0
#
# 为什么自建：Apache Flume 官方没有提供 Docker 镜像，而 apache/hadoop 镜像
#             只解了 hadoop tarball，不含 Flume。所以必须自己构建。
# 维护人：A（组长）　|　2026-11-20
# ==============================================================================
FROM apache/hadoop:3.3.6

ARG FLUME_VERSION=1.11.0
ARG FLUME_URL=https://archive.apache.org/dist/flume/${FLUME_VERSION}/apache-flume-${FLUME_VERSION}-bin.tar.gz

USER root

RUN set -eux; \
    apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*; \
    mkdir -p /opt/flume /var/log/flume; \
    curl -fsSL -o /tmp/flume.tgz "${FLUME_URL}"; \
    tar -xzf /tmp/flume.tgz -C /opt/flume --strip-components=1; \
    rm -f /tmp/flume.tgz; \
    ln -sf /opt/flume/bin/flume-ng /usr/local/bin/flume-ng; \
    chown -R root:root /opt/flume /var/log/flume

ENV FLUME_HOME=/opt/flume
ENV FLUME_CLASSPATH=/opt/flume/lib
ENV PATH=$FLUME_HOME/bin:$PATH

EXPOSE 41414 41415

CMD ["bash", "-c", "flume-ng version"]
