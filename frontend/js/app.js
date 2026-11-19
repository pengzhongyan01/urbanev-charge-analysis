/* ==============================================================================
 * app.js —— 前端主逻辑（骨架模板）
 *
 * 维护人：C（贺欢欢）　|　骨架由 A（彭忠燕）提供，2026-11-19
 *
 * 结构：
 *   1. 页面初始化
 *   2. 筛选条件管理
 *   3. 六个图表的加载与渲染
 *   4. 交互（筛选联动、时钟、状态指示）
 *
 * ⚠️ 待办（贺欢欢）：
 *   - 补齐 6 个接口的具体调用（接口路径见 docs/contracts/03-接口规范.md）
 *   - 深圳地图底图（用 ECharts geo + 275 个分区的经纬度散点/热力图）
 *   - 筛选联动：改日期/时段后所有图表同步刷新
 * ============================================================================== */

(function () {
    'use strict';

    /* ---------------- 全局状态 ---------------- */
    const STATE = {
        filters: {
            startDate: '2022-09-01',
            endDate: '2023-02-28',
            hourRange: '',
            zoneId: '',
            priceType: ''
        },
        charts: {},
        regionCache: null
    };

    /* ---------------- 1. 初始化 ---------------- */
    document.addEventListener('DOMContentLoaded', function () {
        initClock();
        checkStatus();
        bindEvents();
        loadAll();
    });

    /* ---------------- 2. 筛选条件 ---------------- */
    function getFilters() {
        STATE.filters = {
            startDate: document.getElementById('startDate').value,
            endDate: document.getElementById('endDate').value,
            hourRange: document.getElementById('hourSelect').value,
            zoneId: document.getElementById('regionSelect').value,
            priceType: document.getElementById('priceTypeSelect').value
        };
        return STATE.filters;
    }

    function bindEvents() {
        document.getElementById('btnQuery').addEventListener('click', function () {
            console.log('[筛选]', getFilters());
            loadAll();
        });

        document.getElementById('btnReset').addEventListener('click', function () {
            document.getElementById('startDate').value = '2022-09-01';
            document.getElementById('endDate').value = '2023-02-28';
            document.getElementById('hourSelect').value = '';
            document.getElementById('regionSelect').value = '';
            document.getElementById('priceTypeSelect').value = '';
            loadAll();
        });
    }

    /* ---------------- 3. 加载全部数据 ---------------- */
    async function loadAll() {
        const f = getFilters();
        console.log('[加载] 筛选条件:', f);

        await Promise.all([
            loadKpi(f),
            loadHeatmap(f),
            loadHourly(f),
            loadImbalance(f),
            loadPriceElasticity(f),
            loadForecast(f),
            loadSuggestion(f)
        ]);
    }

    /* ---------------- 4. KPI 指标卡 ---------------- */
    async function loadKpi(f) {
        const data = await safeQuery(() => apiGet('/dashboard/kpi', f), '#kpiRow');
        if (!data) return;

        setText('#kpiStations', formatNumber(data.stationCount));
        setText('#kpiOccupancy', formatPercent(data.avgOccupancy));
        setText('#kpiVolume', formatCompact(data.totalVolume));
        setText('#kpiDuration', formatNumber(data.avgDuration, 2));
        setText('#kpiImbalance', formatNumber(data.imbalanceZones));

        // 填充分区下拉框
        if (!STATE.regionCache && data.regions) {
            STATE.regionCache = data.regions;
            populateRegionSelect(data.regions);
        }
    }

    function populateRegionSelect(regions) {
        const sel = document.getElementById('regionSelect');
        regions.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.zoneId;
            opt.textContent = `${r.zoneId}（${r.pileCount || '?'} 桩）`;
            sel.appendChild(opt);
        });
    }

    /* ---------------- 5. 底图加载 ---------------- */
    /**
     * 加载深圳行政区划轮廓作为空间参考底图
     *
     * ⚠️ 注意：底图是深圳市 9 个行政区，而数据是 275 个交通分区，
     *    两者是不同划分体系。本系统用经纬度定位散点，不做分区与行政区的对应。
     */
    async function loadBaseMap() {
        if (echarts.getMap('shenzhen')) return true;   // 已注册

        try {
            const res = await fetch('assets/shenzhen_440300_full.json');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const geoJson = await res.json();

            echarts.registerMap('shenzhen', {
                type: 'FeatureCollection',
                features: (geoJson.features || []).map(f => ({
                    type: 'Feature',
                    properties: { name: f.properties.name },
                    geometry: {
                        type: 'Polygon',
                        // ECharts 5 不支持 MultiPolygon 嵌套，需展平一层
                        coordinates: f.geometry.type === 'MultiPolygon'
                            ? f.geometry.coordinates.flat()
                            : f.geometry.coordinates
                    }
                }))
            });
            console.log('[底图] 深圳行政区划已加载');
            return true;
        } catch (e) {
            console.warn('[底图] 加载失败，将使用散点降级方案:', e.message);
            return false;
        }
    }

    /* ---------------- 6. 热力图 / 地图 ---------------- */
    async function loadHeatmap(f) {
        await loadBaseMap();

        const data = await safeQuery(() => apiGet('/zones/occupancy', f), '#chartHeatmap');
        if (!data) return;

        const zones = data.zones || [];
        if (!zones.length) return;

        // 有底图 → 散点叠加；无底图 → 纯散点降级
        if (echarts.getMap('shenzhen')) {
            STATE.charts.heatmap = initChart('chartHeatmap', baseOption({
                tooltip: {
                    trigger: 'item',
                    formatter: p => {
                        const z = zones[p.dataIndex];
                        if (!z) return '';
                        return `<b>分区 ${z.zoneId}</b><br>` +
                               `占用率：${formatPercent(z.avgOccupancy)}<br>` +
                               `充电桩：${z.chargeCount} 个<br>` +
                               `POI 总数：${z.poiTotal || '--'}`;
                    }
                },
                legend: { show: false },
                geo: {
                    map: 'shenzhen',
                    roam: false,
                    itemStyle: {
                        areaColor: '#0f2038',
                        borderColor: '#1e3a5f',
                        borderWidth: 1
                    },
                    emphasis: {
                        itemStyle: { areaColor: '#1a3a5f' },
                        label: { show: false }
                    },
                    label: { show: false }
                },
                series: [{
                    type: 'scatter',
                    coordinateSystem: 'geo',
                    symbolSize: d => 5 + (d[2] || 0) * 14,
                    data: zones.map(z => [z.longitude, z.latitude, z.avgOccupancy]),
                    itemStyle: {
                        color: p => {
                            const t = p.value[2] || 0;
                            if (t > 0.7) return '#ff6b35';   // 紧张
                            if (t > 0.4) return '#00d4ff';   // 正常
                            return '#22c55e';                 // 闲置
                        },
                        opacity: 0.85
                    },
                    emphasis: { scale: 1.5 }
                }]
            }));
            return;
        }

        STATE.charts.heatmap = initChart('chartHeatmap', baseOption({
            tooltip: {
                trigger: 'item',
                formatter: p => {
                    const d = zones[p.data.value[2]] || {};
                    return `${d.zoneId} 分区<br>` +
                           `占用率：${formatPercent(d.avgOccupancy)}<br>` +
                           `充电桩：${d.chargeCount || '--'} 个<br>` +
                           `POI 总数：${d.poiTotal || '--'}`;
                }
            },
            visualMap: {
                min: 0, max: 1,
                calculable: true,
                orient: 'horizontal',
                left: 'center',
                bottom: 8,
                inRange: { color: ['#0a1628', '#1e3a5f', '#0891b2', '#00d4ff', '#a7f3d0'] },
                textStyle: { color: '#8fa8c8' }
            },
            geo: {
                map: 'shenzhen',
                roam: false,
                itemStyle: { areaColor: '#0f2038', borderColor: '#1e3a5f' },
                emphasis: { itemStyle: { areaColor: '#1a3a5f' } }
            },
            series: [{
                type: 'heatmap',
                coordinateSystem: 'geo',
                data: zones.map(z => [
                    z.longitude, z.latitude,
                    [z.longitude, z.latitude, z.avgOccupancy]
                ]),
                pointSize: 10
            }]
        }));

        // 如果没有地图 GeoJSON，退化为纯散点图
        if (!STATE.charts.heatmap) {
            renderScatterFallback('chartHeatmap', zones);
        }
    }

    /** 没有深圳地图底图时的散点降级方案 */
    function renderScatterFallback(domId, zones) {
        STATE.charts[domId] = initChart(domId, baseOption({
            tooltip: {
                trigger: 'item',
                formatter: p => `${zones[p.dataIndex].zoneId}<br>占用率 ${formatPercent(p.value[2])}`
            },
            xAxis: { type: 'value', name: '经度', axisLabel: { color: '#8fa8c8' } },
            yAxis: { type: 'value', name: '纬度', axisLabel: { color: '#8fa8c8' } },
            series: [{
                type: 'scatter',
                symbolSize: d => 6 + d[2] * 18,
                data: zones.map(z => [z.longitude, z.latitude, z.avgOccupancy]),
                itemStyle: {
                    color: p => {
                        const t = p.value[2] || 0;
                        return t > 0.7 ? '#ff6b35' : t > 0.4 ? '#00d4ff' : '#22c55e';
                    }
                }
            }]
        }));
    }

    /* ---------------- 7. 24 小时供需曲线 ---------------- */
    async function loadHourly(f) {
        const data = await safeQuery(() => apiGet('/charts/hourly', f), '#chartHourly');
        if (!data) return;

        const rows = data.hourly || [];
        const hours = rows.map(r => r.hourOfDay);
        const demand = rows.map(r => Number(r.demandShare || 0));
        const supply = rows.map(r => Number(r.supplyShare || 0));
        const occupancy = rows.map(r => Number(r.avgOccupancy || 0));

        STATE.charts.hourly = initChart('chartHourly', baseOption({
            legend: { data: ['需求份额', '运力份额', '平均占用率'] },
            xAxis: {
                type: 'category', data: hours.map(h => h + '时'),
                axisLabel: { color: '#8fa8c8' },
                axisLine: { lineStyle: { color: '#1e3a5f' } }
            },
            yAxis: {
                type: 'value', axisLabel: { color: '#8fa8c8' },
                splitLine: { lineStyle: { color: 'rgba(30,58,95,.5)' } }
            },
            series: [
                {
                    name: '需求份额', type: 'line', data: demand,
                    smooth: true, areaStyle: { opacity: 0.15 },
                    itemStyle: { color: CHART_COLORS[0] },
                    lineStyle: { width: 2.5 }
                },
                {
                    name: '运力份额', type: 'line', data: supply,
                    smooth: true, itemStyle: { color: CHART_COLORS[1] },
                    lineStyle: { width: 2.5, type: 'dashed' }
                },
                {
                    name: '平均占用率', type: 'line', data: occupancy,
                    smooth: true, yAxisIndex: 0,
                    itemStyle: { color: CHART_COLORS[3] }
                }
            ]
        }));
    }

    /* ---------------- 8. 失衡指数 TOP10 ---------------- */
    async function loadImbalance(f) {
        const data = await safeQuery(() => apiGet('/charts/imbalance', f), '#chartImbalance');
        if (!data) return;

        const rows = (data.top || []).slice().reverse();

        STATE.charts.imbalance = initChart('chartImbalance', baseOption({
            grid: { left: 60, right: 40, top: 30, bottom: 30 },
            tooltip: {
                trigger: 'axis',
                formatter: p => {
                    const d = rows[p[0].dataIndex];
                    return `${d.zoneId} 分区<br>失衡指数：${Number(d.imbalance).toFixed(4)}<br>` +
                           `需求份额：${formatPercent(d.demandShare)}<br>` +
                           `运力份额：${formatPercent(d.supplyShare)}`;
                }
            },
            xAxis: {
                type: 'value', name: '失衡指数',
                axisLabel: { color: '#8fa8c8' },
                splitLine: { lineStyle: { color: 'rgba(30,58,95,.5)' } }
            },
            yAxis: {
                type: 'category',
                data: rows.map(r => r.zoneId),
                axisLabel: { color: '#8fa8c8' },
                axisLine: { lineStyle: { color: '#1e3a5f' } }
            },
            series: [{
                type: 'bar',
                data: rows.map(r => ({
                    value: Number(r.imbalance),
                    itemStyle: {
                        color: Number(r.imbalance) > 0 ? '#ff6b35' : '#22c55e'
                    }
                })),
                barMaxWidth: 20,
                label: {
                    show: true, position: 'right',
                    formatter: p => p.value.toFixed(3),
                    color: '#8fa8c8', fontSize: 10
                }
            }]
        }));
    }

    /* ---------------- 9. 电价弹性对比 ---------------- */
    async function loadPriceElasticity(f) {
        const data = await safeQuery(() => apiGet('/charts/price-elasticity', f), '#chartPriceElasticity');
        if (!data) return;

        const tou = data.tou || [];
        const flat = data.flat || [];

        STATE.charts.priceElasticity = initChart('chartPriceElasticity', baseOption({
            legend: { data: ['分时电价区', '固定电价区'] },
            xAxis: {
                type: 'category', data: tou.map(r => r.hourOfDay + '时'),
                axisLabel: { color: '#8fa8c8' },
                axisLine: { lineStyle: { color: '#1e3a5f' } }
            },
            yAxis: {
                type: 'value', name: '平均占用率',
                axisLabel: { color: '#8fa8c8' },
                splitLine: { lineStyle: { color: 'rgba(30,58,95,.5)' } }
            },
            series: [
                {
                    name: '分时电价区', type: 'line',
                    data: tou.map(r => Number(r.avgOccupancy)),
                    smooth: true, itemStyle: { color: CHART_COLORS[1] },
                    areaStyle: { opacity: 0.18 }, lineStyle: { width: 2.5 }
                },
                {
                    name: '固定电价区', type: 'line',
                    data: flat.map(r => Number(r.avgOccupancy)),
                    smooth: true, itemStyle: { color: CHART_COLORS[0] },
                    lineStyle: { width: 2.5, type: 'dashed' }
                }
            ]
        }));

        // 显示弹性指标
        if (data.summary) {
            const s = data.summary;
            document.querySelector('#chartPriceElasticity .chart-tip').innerHTML =
                `分时电价区峰谷差 ${Number(s.touElasticity).toFixed(4)}　|　` +
                `固定电价区峰谷差 ${Number(s.flatElasticity).toFixed(4)}　|　` +
                `价差 ${Number(s.touGap - s.flatGap).toFixed(4)}`;
        }
    }

    /* ---------------- 10. 需求预测曲线 ---------------- */
    async function loadForecast(f) {
        const data = await safeQuery(() => apiGet('/charts/forecast', f), '#chartForecast');
        if (!data) return;

        const series = data.series || [];

        STATE.charts.forecast = initChart('chartForecast', baseOption({
            legend: { data: ['预测值', '实际值'] },
            xAxis: {
                type: 'category',
                data: series.map(s => s.forecastDate),
                axisLabel: { color: '#8fa8c8' },
                axisLine: { lineStyle: { color: '#1e3a5f' } }
            },
            yAxis: {
                type: 'value', name: '充电量 kWh',
                axisLabel: { color: '#8fa8c8' },
                splitLine: { lineStyle: { color: 'rgba(30,58,95,.5)' } }
            },
            series: [
                {
                    name: '预测值', type: 'line',
                    data: series.map(s => Number(s.predictVolume)),
                    smooth: true, itemStyle: { color: CHART_COLORS[0] },
                    lineStyle: { width: 2, type: 'dashed' }
                },
                {
                    name: '实际值', type: 'line',
                    data: series.map(s => Number(s.actualVolume)),
                    smooth: true, itemStyle: { color: CHART_COLORS[2] },
                    lineStyle: { width: 2.5 }
                }
            ]
        }));

        if (data.mape != null) {
            document.getElementById('predictMape').innerHTML =
                `MAPE = ${Number(data.mape).toFixed(2)}%`;
        }
    }

    /* ---------------- 11. 布点建议 ---------------- */
    async function loadSuggestion(f) {
        const data = await safeQuery(() => apiGet('/charts/suggestions', f), '#chartSuggestion');
        if (!data) return;

        const rows = (data.suggestions || []).slice(0, 30);
        const container = document.getElementById('chartSuggestion');
        if (!container) return;

        container.innerHTML = `
            <table style="width:100%;font-size:12px;border-collapse:collapse">
                <thead>
                    <tr style="color:#8fa8c8;text-align:left;border-bottom:1px solid #1e3a5f">
                        <th style="padding:6px">优先级</th>
                        <th style="padding:6px">分区</th>
                        <th style="padding:6px">现有</th>
                        <th style="padding:6px">建议</th>
                        <th style="padding:6px">理由</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => `
                        <tr style="border-bottom:1px solid rgba(30,58,95,.4)">
                            <td style="padding:6px;color:${r.priority <= 10 ? '#ff6b35' : '#8fa8c8'}">
                                ${r.priority}
                            </td>
                            <td style="padding:6px;color:#00d4ff">${r.zoneId}</td>
                            <td style="padding:6px">${r.currentPiles}</td>
                            <td style="padding:6px;color:#22c55e;font-weight:600">
                                ${r.suggestedPiles}
                            </td>
                            <td style="padding:6px;color:#8fa8c8;font-size:11px">${r.reason}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    /* ---------------- 工具 ---------------- */
    function setText(sel, text) {
        const el = document.querySelector(sel);
        if (el) el.textContent = text;
    }

    // 暴露到全局，便于控制台调试
    window.UEV = { STATE, loadAll, loadKpi, loadBaseMap, loadHeatmap, loadHourly,
                    loadImbalance, loadPriceElasticity, loadForecast, loadSuggestion };
})();
