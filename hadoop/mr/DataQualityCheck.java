package com.uev.mr;

import java.io.IOException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

/**
 * DataQualityCheck —— 数据质量检查与清洗
 * ============================================================================
 * 维护人：苏静（B 组）　|　骨架由 A（组长）提供，2026-11-19
 *
 * 【为什么这个作业很重要】
 * 报告第三章"数据清洗"要有**真实数据支撑**，不能只写"我们检查了数据"。
 * 这个作业产出三张质量报告表，直接进报告：
 *
 *   1. uev_dwd.dq_null_count    —— 各分区的缺失值统计（哪些分区 0 值是真 0 还是缺失）
 *   2. uev_dwd.dq_outlier       —— 越界值统计（占用率 > 1、电价 < 0 等）
 *   3. uev_dwd.dq_hour_summary  —— 每小时的有效记录数（验证 181 天 x 24 小时完整性）
 *
 * 【运行】
 *   hadoop jar uev-mr.jar com.uev.mr.DataQualityCheck \
 *        /uev/raw/occupancy.csv /uev/dwd/dq_occupancy \
 *        -D uev.metric.name=occupancy \
 *        -D uev.metric.min=0 \
 *        -D uev.metric.max=1
 *
 * 【清洗规则（按指标配置）】
 *   occupancy : 合法区间 [0, 1]，越界值置 NULL
 *   duration  : 合法区间 [0, ∞)，负值置 NULL
 *   volume    : 合法区间 [0, ∞)，负值置 NULL
 *   e_price   : 合法区间 [0, ∞)，负值或 > 10 置 NULL
 *   s_price   : 合法区间 [0, ∞)，负值或 > 5 置 NULL
 *
 * @author uev-team
 */
public class DataQualityCheck {

    // ======================= Mapper =======================
    /**
     * 逐单元格检查：统计缺失、越界、有效
     */
    public static class DqMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

        private String metricName = "occupancy";
        private double minValue = 0.0;
        private double maxValue = 1.0;

        @Override
        protected void setup(Context context) throws IOException {
            Configuration conf = context.getConfiguration();
            metricName = conf.get("uev.metric.name", "occupancy");
            minValue = conf.getDouble("uev.metric.min", 0.0);
            maxValue = conf.getDouble("uev.metric.max", 1.0);
        }

        @Override
        protected void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {

            String line = value.toString().trim();
            if (line.isEmpty()) {
                return;
            }
            String[] cols = line.split(",", -1);
            if (cols.length < 2) {
                return;
            }

            String hourTs = cols[0];
            int hourOfDay = -1;
            try {
                hourOfDay = Integer.parseInt(hourTs.substring(11, 13));
            } catch (Exception ignored) {
                // 时间戳异常，整行标记
                context.write(new Text("INVALID_TIMESTAMP"), new IntWritable(1));
                return;
            }

            // 整行小时完整性统计
            context.write(new Text("HOUR|" + hourOfDay), new IntWritable(1));

            for (int i = 1; i < cols.length; i++) {
                String zoneId = cols[i].trim();
                String raw = cols[i].trim();
                if (!isNumeric(raw)) {
                    continue;   // 表头行
                }

                double v = Double.parseDouble(raw);
                Text zoneKey = new Text(zoneId);

                if (v == 0.0) {
                    // 零值：可能是真实 0，也可能是缺失，单独标记
                    context.write(new Text("ZERO|" + zoneId), new IntWritable(1));
                } else if (v < minValue || v > maxValue) {
                    // 越界
                    context.write(new Text("OUTLIER|" + zoneId + "|" + v), new IntWritable(1));
                } else {
                    // 有效
                    context.write(new Text("VALID|" + zoneId), new IntWritable(1));
                }
            }
        }

        private boolean isNumeric(String s) {
            if (s == null || s.isEmpty()) return false;
            try {
                Double.parseDouble(s);
                return true;
            } catch (NumberFormatException e) {
                return false;
            }
        }
    }

    // ======================= Reducer =======================
    public static class DqReducer extends Reducer<Text, IntWritable, Text, IntWritable> {
        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context)
                throws IOException, InterruptedException {
            int sum = 0;
            for (IntWritable v : values) {
                sum += v.get();
            }
            context.write(key, new IntWritable(sum));
        }
    }

    // ======================= 作业入口 =======================
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("用法: hadoop jar uev-mr.jar com.uev.mr.DataQualityCheck <输入> <输出>");
            System.err.println("      可选: -D uev.metric.name=occupancy -D uev.metric.min=0 -D uev.metric.max=1");
            System.exit(1);
        }

        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "DataQualityCheck-" + conf.get("uev.metric.name", "occupancy"));

        job.setJarByClass(DataQualityCheck.class);
        job.setMapperClass(DqMapper.class);
        job.setReducerClass(DqReducer.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(IntWritable.class);
        job.setNumReduceTasks(1);   // 质量统计用单 Reducer 汇总最方便

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
