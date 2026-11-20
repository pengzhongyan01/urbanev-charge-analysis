# hadoop/lib —— Hadoop 运行时 jar（编译 MR 作业用）

MR 作业编译需要 `hadoop-common` / `hadoop-mapreduce-client-core` 等 jar。
有两种拿到它们的方式（RUNBOOK 步骤 7.1 用的是方式 A）：

## 方式 A：从运行中的容器里拷出来（推荐，版本一定对得上）

```bash
mkdir -p hadoop/lib
docker cp uev-namenode:/opt/hadoop/share/hadoop/common/lib/. hadoop/lib/
docker cp uev-namenode:/opt/hadoop/share/hadoop/mapreduce/hadoop-mapreduce-client-core-3.3.6.jar hadoop/lib/
docker cp uev-namenode:/opt/hadoop/share/hadoop/common/lib/commons-configuration2-*.jar hadoop/lib/
```

## 方式 B：从 Apache 官网下 tarball 后取

```bash
curl -O https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -xzf hadoop-3.3.6.tar.gz
cp hadoop-3.3.6/share/hadoop/common/lib/*.jar hadoop/lib/
```

> ★ `.gitignore` 已排除 `*.jar`，这些 jar 不会进仓库，组员自己拷一次即可。
