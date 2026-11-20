package com.uev.mr;

import java.io.IOException;
import java.io.BufferedReader;
import java.io.FileReader;
import java.util.HashMap;
import java.util.Map;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.util.GenericOptionsParser;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

/**
 * PoiZoneJoin —— POI 空间连接聚合（71 万 POI 落到 275 个分区）
 * ============================================================================
 * 维护人：苏静（B 组）　|　骨架由 A（组长）提供，2026-11-19
 *
 * 【为什么必须用 MR，不能用 Hive】
 *   poi.csv 有 71 万行，需要用经纬度匹配到最近的交通分区。
 *   如果在 Hive 里做笛卡尔积 join（71万 × 275 = 1.96 亿行），
 *   集群压力大且慢。用 MR 做 Map 端广播维表 + Reduce 端聚合，效率高得多。
 *   而且这个作业本身就是"空间连接"的教学案例，进报告很扎实。
 *
 * 【算法】
 *   Map 端（读 POI）：
 *     对每个 POI，遍历 275 个分区，计算球面距离，取最近的那个分区
 *     输出 (zone_id, poi_type) → 1
 *
 *   Reduce 端：
 *     按 zone_id 聚合，输出各分区的三类 POI 数量
 *
 * 【性能优化】
 *   - 分区坐标表只有 275 行，直接在 setup() 里加载到内存（广播）
 *   - 距离用 haversine 公式
 *   - 71 万 POI × 275 次距离计算 ≈ 1.96 亿次 —— 单 Mapper 大约 1-2 分钟，可接受
 *
 * 【运行】
 *   # 1. 先把 inf.csv 放到 HDFS
 *   hdfs dfs -put -f data/raw/inf.csv /uev/ods/inf/
 *   # 2. 运行
 *   hadoop jar uev-mr.jar com.uev.mr.PoiZoneJoin \
 *        /uev/ods/poi/poi.csv /uev/dwd/zone_poi_count \
 *        -D uev.zone.info.path=/uev/ods/inf/inf.csv
 *
 * 【输出格式】
 *   zone_id \t poi_lifestyle \t poi_business \t poi_food \t poi_total
 *
 * @author uev-team
 */
public class PoiZoneJoin {

    // ======================= Mapper =======================
    /**
     * POI → 最近分区
     */
    public static class PoiMapper extends Mapper<LongWritable, Text, Text, IntWritable> {

        /** 分区坐标表：zone_id → [lng, lat] */
        private Map<String, double[]> zoneMap = new HashMap<>();

        /** POI 类别 → 类型编码：0=生活服务 1=商务居住 2=餐饮服务 */
        private static int typeCode(String primaryType) {
            if (primaryType == null) return -1;
            String t = primaryType.toLowerCase().trim();
            if (t.contains("lifestyle")) return 0;
            if (t.contains("business")) return 1;
            if (t.contains("food")) return 2;
            return -1;
        }

        @Override
        protected void setup(Context context) throws IOException {
            Configuration conf = context.getConfiguration();
            String path = conf.get("uev.zone.info.path");

            if (path == null) {
                throw new IOException("必须指定 -D uev.zone.info.path=分区坐标表路径");
            }

            // 从 HDFS 加载 275 个分区坐标
            try (BufferedReader br = new BufferedReader(
                    new FileReader(path.replaceFirst("^hdfs://[^/]+", "")))) {
                String line;
                boolean isHeader = true;
                while ((line = br.readLine()) != null) {
                    line = line.trim();
                    if (line.isEmpty()) continue;
                    if (isHeader) { isHeader = false; continue; }
                    String[] p = line.split(",");
                    if (p.length < 3) continue;
                    try {
                        double lng = Double.parseDouble(p[1]);
                        double lat = Double.parseDouble(p[2]);
                        zoneMap.put(p[0].trim(), new double[]{lng, lat});
                    } catch (NumberFormatException ignored) {
                        // 跳过非法行
                    }
                }
            }

            context.getCounter("PoiJoin", "zones_loaded").increment(zoneMap.size());
        }

        @Override
        protected void map(LongWritable key, Text value, Context context)
                throws IOException, InterruptedException {

            String line = value.toString().trim();
            if (line.isEmpty() || line.startsWith("primary_types")) {
                return;   // 表头
            }

            String[] cols = line.split(",");
            if (cols.length < 3) return;

            int type = typeCode(cols[0]);
            if (type < 0) return;

            double poiLng, poiLat;
            try {
                poiLng = Double.parseDouble(cols[1]);
                poiLat = Double.parseDouble(cols[2]);
            } catch (NumberFormatException e) {
                return;
            }

            // 找最近分区
            String nearest = null;
            double minDist = Double.MAX_VALUE;
            for (Map.Entry<String, double[]> e : zoneMap.entrySet()) {
                double d = haversine(poiLng, poiLat, e.getValue()[0], e.getValue()[1]);
                if (d < minDist) {
                    minDist = d;
                    nearest = e.getKey();
                }
            }

            if (nearest != null) {
                // key = zone_id + "_" + type, value = 1
                context.write(new Text(nearest + "_" + type), new IntWritable(1));
            }
        }

        /** 球面距离（米），Haversine 公式 */
        private double haversine(double lng1, double lat1, double lng2, double lat2) {
            final double R = 6371000.0;
            double dLat = Math.toRadians(lat2 - lat1);
            double dLng = Math.toRadians(lng2 - lng1);
            double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                     + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                     * Math.sin(dLng / 2) * Math.sin(dLng / 2);
            return 2 * R * Math.asin(Math.sqrt(a));
        }
    }

    // ======================= Reducer =======================
    /**
     * 按 zone_id 汇总三类 POI 数量
     */
    public static class PoiReducer extends Reducer<Text, IntWritable, Text, Text> {
        @Override
        protected void reduce(Text key, Iterable<IntWritable> values, Context context)
                throws IOException, InterruptedException {

            String[] parts = key.toString().split("_");
            String zoneId = parts[0];
            int type = Integer.parseInt(parts[1]);

            int count = 0;
            for (IntWritable v : values) {
                count += v.get();
            }

            // 输出：zone_id \t type \t count
            context.write(new Text(zoneId), new Text(type + "\t" + count));
        }
    }

    // ======================= 作业入口 =======================
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("用法: hadoop jar uev-mr.jar com.uev.mr.PoiZoneJoin <POI路径> <输出路径>");
            System.err.println("      必需: -D uev.zone.info.path=/uev/ods/inf/inf.csv");
            System.exit(1);
        }

        Configuration conf = new Configuration();
        // ★ 必须解析 -D 命令行参数，否则 uev.metric.name / uev.zone.info.path 永远取不到
        GenericOptionsParser parser = new GenericOptionsParser(args);
        conf = parser.getConf();
        Job job = Job.getInstance(conf, "PoiZoneJoin");

        job.setJarByClass(PoiZoneJoin.class);
        job.setMapperClass(PoiMapper.class);
        job.setReducerClass(PoiReducer.class);

        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);

        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));

        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
