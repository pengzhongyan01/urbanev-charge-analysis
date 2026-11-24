package com.uev.vo;

import com.uev.entity.VolumeDeviation;
import lombok.Data;

import java.util.List;

/**
 * /api/charts/volume-deviation 的 data 载荷（契约 03 · 2.9）。
 *
 * @author 杨珊珊（D 岗）
 */
@Data
public class VolumeDeviationVO {

    private List<VolumeDeviation> zones;
    private Summary summary;

    @Data
    public static class Summary {
        private Double avgDeviation;
        private Double maxDeviation;
    }

    public static VolumeDeviationVO of(List<VolumeDeviation> zones) {
        VolumeDeviationVO vo = new VolumeDeviationVO();
        vo.setZones(zones);
        Summary s = new Summary();
        if (zones == null || zones.isEmpty()) {
            s.setAvgDeviation(0.0);
            s.setMaxDeviation(0.0);
        } else {
            double sum = 0.0;
            double max = 0.0;
            int cnt = 0;
            for (VolumeDeviation z : zones) {
                if (z.getDeviation() == null) {
                    continue;
                }
                sum += z.getDeviation();
                max = Math.max(max, z.getDeviation());
                cnt++;
            }
            s.setAvgDeviation(cnt == 0 ? 0.0 : sum / cnt);
            s.setMaxDeviation(max);
        }
        vo.setSummary(s);
        return vo;
    }
}
