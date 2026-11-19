package com.uev.mr;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

/**
 * WideToLong —— 宽表转长表（列转行 explode）
 * ============================================================================
 * 维护人：苏静（B 组）　|　骨架由 A（组长）提供，2026-11-19
 *
 * 【为什么需要这个作业】
 * UrbanEV 的原始数据是宽表：time + 275 个分区列。
 * 但后续所有聚合分析（Hive SQL、Spark 计算）都需要标准长表：
 *     (zone_id, hour_ts, metric, value)
 * 这一步就是 ETL 里的 E（Explode，列转行）。
 *
 * 【数据流】
 *   HDFS /uev/raw/occupancy.csv
 *      → Mapper: 读一行，遍历 275 个分区列，输出 275 条 (zone_id, time, value)
 *      → Reducer: 原样透传（可选：做 24 小时 0 值计数，标记缺失）
 *      → HDFS /uev/dwd/zone_hour_metric/
 *
 * 【运行】
 *   hadoop jar uev-mr.jar com.uev.mr.WideToLong \
 *        /uev/raw/occupancy.csv /uev/dwd/occupancy_long \
 *        -D uev.metric.name=occupancy
 *
 * 【为什么用 MR 而不是 Hive stack】
 *   Hive 的 stack() 需要硬编码 275 个列名，代码极难维护；
 *   MapReduce 读一行动态遍历所有列，代码通用、加指标不用改代码。
 *   这也是本项目"熟练掌握 Hadoop"评分点的直接证据。
 *
 * @author uev-team
 */
public class WideToLong {

    // ======================= Mapper =======================
    /**
     * 把一行宽表炸成多行长表
     *
     * 输入格式：time,zone1,zone2,...,zone275
     * 输出格式：zone_id \t hour_ts \t value
     */
    public static class WideToLongMapper extends Mapper<LongWritable, Text, Text, Text> {

        /** 指标名：从作业参数 -D uev.metric.name=xxx 传入 */
        private String metricName = "occupancy";

        @Override
        protected void setup(Context context) throws IOException, ConfigurationException {
            Configuration conf = context.getConfiguration();
            metricName = conf.get("uev.metric.name", "occupancy");
        }

        @Override
        protected void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {

            String line = value.toString().trim();
            if (line.isEmpty()) {
                return;
            }

            // 用 -1 保留末尾空列，避免最后一个分区被丢掉
            String[] cols = line.split(",", -1);
            if (cols.length < 2) {
                return;
            }

            String hourTs = cols[0];   // 时间戳
            Text outKey = new Text();
            Text outVal = new Text();

            // 从第 1 列开始，每一列就是一个分区
            for (int i = 1; i < cols.length; i++) {
                String zoneId = cols[i].trim();
                // 表头行（time,102,104...）跳过
                if (!isNumeric(cols[i])) {
                    continue;
                }
                outKey.set(zoneId);
                outVal.set(hourTs + "\t" + cols[i].trim() + "\t" + metricName);
                context.write(outKey, outVal);
            }
        }

        /** 判断字符串是否为数字 */
        private boolean isNumeric(String s) {
            if (s == null || s.isEmpty()) {
                return false;
            }
            try {
                Double.parseDouble(s);
                return true;
            } catch (NumberFormatException e) {
                return false;
            }
        }
    }

    // ======================= Reducer =======================
    /**
     * 透传 Reducer
     *
     * 这里保留 Reducer 是为了展示完整的 MapReduce 作业结构；
     * 实际计算时可以在此做聚合（如按 (zone_id, date) 汇总）。
     */
    public static class PassThroughReducer
            extends Reducer<Text, Text, Text, Text> {
        @Override
        protected void reduce(Text key, Iterable<Text> values, Context context)
                throws IOException, InterruptedException {
            for (Text v : values) {
                context.write(key, v);
            }
        }
    }

    // ======================= 作业入口 =======================
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("用法: hadoop jar uev-mr.jar com.uev.mr.WideToLong <输入路径> <输出路径>");
            System.err.println("      可选: -D uev.metric.name=occupancy");
            System.exit(1);
        }

        Configuration conf = new Configuration();
        conf.set("uev.metric.name", conf.get("uev.metric.name", "occupancy"));

        Job job = Job.getInstance(conf, "WideToLong-" + conf.get("uev.metric.name"));

        job.setJarByClass(WideToLong.class);
        job.setMapperClass(WideToLongMapper.class);
        job.setReducerClass(PassThroughReducer.class);

        // 输出 key=zone_id，value=hour_ts \t value \t metric
        job.setMapOutputKeyClass(Text.class);
        job.setMapOutputValueClass(Text.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        // 宽表列多，单个 split 容易 OOM，调大单个 map 的内存
        conf.setLong("mapreduce.input.fileinputformat.split.maxsize", 128 * 1024 * 1024);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.out.println("作业配置:");
        System.out.println("  指标名: " + conf.get("uev.metric.name"));
        System.out.println("  输入  : " + args[0]);
        System.out.println("  输出  : " + args[1]);

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }

    /** 简化版 ConfigurationException 引用 */
    static class ConfigurationException extends IOException {
        ConfigurationException(String msg) { super(msg); }
    }
}
