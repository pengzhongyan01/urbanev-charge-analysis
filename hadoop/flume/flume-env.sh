#!/usr/bin/env bash
# ==============================================================================
# flume-env.sh —— Flume 环境变量
#
# ★ 为什么叫 .sh 不是 .conf：
#   Flume 的 bin/flume-ng 只 source $FLUME_HOME/conf/flume-env.sh，
#   .conf 这个名字没有任何程序会读。原来的 flume-env.conf 是个死文件。
#
# 维护人：A（组长）　|　2026-11-20
# ==============================================================================

# ---- JVM 参数（采集端 1-2G 够用）----
export JAVA_OPTS="-Xms512m -Xmx2048m -Dcom.sun.management.jmxremote"

# ---- 日志 ----
export FLUME_LOG_DIR=/var/log/flume
export FLUME_LOG_FILE=${FLUME_LOG_DIR}/flume-agent.log

# ---- 组件类路径 ----
# ★ 只列额外的 jar 目录。plugins.d 是 Flume 自己的 PluginManager 扫描的目录，
#   塞进 FLUME_CLASSPATH 会让 Flume 把「目录」当 jar 加进 classpath，破坏插件加载。
export FLUME_CLASSPATH=$FLUME_HOME/lib

# ---- 采集端目录（与 docker-compose.yml 里的 flume 服务保持一致）----
export FLUME_SOURCE_DIR=/data/urbanev
export FLUME_HDFS_BASE=hdfs://namenode:8020/uev/raw
export FLUME_CHECKPOINT_DIR=/opt/flume/checkpoint
