/* ==============================================================================
 * page-zones.js —— 供需失衡分析页
 *
 * 维护人：C（贺欢欢）　|　框架由 A（彭忠燕）提供，2026-11-24
 *
 * ★ C 岗 TODO 说明（本文件里的数据源有两条路径，二选一即可）：
 *   路径 A（推荐，答辩现场最稳）：前端直接读静态 CSV，不依赖后端
 *          → 数据文件：frontend/data/*.csv（由 A 岗从 ADS 表导出）
 *   路径 B：调后端接口
 *          → GET /api/charts/imbalance、GET /api/zones/occupancy
 *   下方 DATA_MODE 常量控制切换。
 *
 * ★ 待 C 岗完成的三件事：
 *   1. 核对 KPI 数值与图表配色
 *   2. 把「导出 CSV」按钮接上真实导出（含筛选条件）
 *   3. 确认时段筛选是否联动到失衡图
 * ============================================================================== */

const DATA_MODE = 'static';   // 'static' | 'api'

const ZONES_CSV = 'data/imbalance_index.csv';
const OCC_CSV   = 'data/zone_occupancy.csv';

let ZONES = [];       // 失衡记录
let OCC = {};         // zone_id → {avg_occupancy, charge_count, ...}
let CHARTS = {};      // echarts 实例

/* ---------------- 数据加载 ---------------- */

async function loadStatic(path) {
    const res = await fetch(path);
    if (!res.ok) throw new Error(`加载失败 ${path}（HTTP ${res.status}）`);
    return res.text();
}

function parseCSV(text) {
    const lines = text.replace(/^\uFEFF/, '').trim().split('\n');
    const head = lines[0].split(',').map(s => s.trim().replace(/^\uFEFF/, ''));
    return lines.slice(1).map(line => {
        const cells = line.split(',');
        const o = {};
        head.forEach((h, i) => { o[h] = (cells[i] ?? '').trim(); });
        return o;
    });
}

async function loadData() {
    if (DATA_MODE === 'static') {
        const [zText, oText] = await Promise.all([loadStatic(ZONES_CSV), loadStatic(OCC_CSV)]);
        // ★ E 岗契约口径表的真实列名：demand_share / supply_share（无 dt / longitude）
        ZONES = parseCSV(zText).map(r => ({
            zone_id: r.zone_id,
            hour_of_day: +r.hour_of_day || 0,
            imbalance: +r.imbalance || 0,
            demand: +r.demand_share || 0,
            supply: +r.supply_share || 0,
            rank_no: +r.rank_no,
        }));
        parseCSV(oText).forEach(r => {
            OCC[r.zone_id] = {
                avg_occupancy: +r.avg_occupancy || 0,
                max_occupancy: +r.max_occupancy || 0,
                charge_count: +r.charge_count || 0,
                longitude: +r.longitude,
                latitude: +r.latitude,
            };
        });
    } else {
        const [z, o] = await Promise.all([
            apiGet('/charts/imbalance'),
            apiGet('/zones/occupancy'),
        ]);
        ZONES = (z.data || z).map(r => ({ ...r, imbalance: +r.imbalance }));
        (o.data || o).forEach(r => { OCC[r.zone_id] = r; });
    }
}

/* ---------------- 筛选 ---------------- */

function getFilters() {
    const zone = document.getElementById('zoneSelect').value;
    const hour = document.getElementById('hourSelect').value;
    const sort = document.getElementById('sortSelect').value;
    let rows = ZONES.slice();

    if (zone) rows = rows.filter(r => String(r.zone_id) === zone);
    if (hour) {
        const [a, b] = hour.split('-').map(Number);
        rows = rows.filter(r => r.hour_of_day >= a && r.hour_of_day <= b);
    }
    if (sort === 'desc') rows.sort((x, y) => y.imbalance - x.imbalance);
    else if (sort === 'asc') rows.sort((x, y) => x.imbalance - y.imbalance);
    else rows.sort((x, y) => Math.abs(y.imbalance) - Math.abs(x.imbalance));
    return rows;
}

/** 按分区去重取 TOP N（同一分区只保留最紧张的那个时段） */
function topByZone(rows, n) {
    const seen = new Set();
    const out = [];
    for (const r of rows) {
        if (seen.has(r.zone_id)) continue;
        seen.add(r.zone_id);
        out.push(r);
        if (out.length >= n) break;
    }
    return out;
}

/* ---------------- KPI ---------------- */

function renderKPI(rows) {
    // ★ 按分区去重：一个分区只要有任一时段供不应求就算「供不应求分区」
    const shortZones = new Set(rows.filter(r => r.imbalance > 0).map(r => r.zone_id));
    const idleZones  = new Set(rows.filter(r => r.imbalance < 0).map(r => r.zone_id));
    const shortage = rows.filter(r => r.imbalance > 0);
    const idle = rows.filter(r => r.imbalance < 0);
    const peak = rows.reduce((a, b) => (b.imbalance > (a?.imbalance ?? -Infinity) ? b : a), null);
    const avg = rows.length ? rows.reduce((s, r) => s + r.imbalance, 0) / rows.length : 0;

    document.getElementById('kpiShortage').textContent = shortZones.size;
    document.getElementById('kpiShortageSub').textContent =
        `占 ${new Set(rows.map(r => r.zone_id)).size} 个分区的 `
        + `${(shortZones.size / Math.max(new Set(rows.map(r => r.zone_id)).size, 1) * 100).toFixed(1)}%`;
    document.getElementById('kpiPeak').textContent = peak ? peak.imbalance.toFixed(4) : '—';
    document.getElementById('kpiPeakSub').textContent =
        peak ? `出现在 ${peak.zone_id} 区（${String(peak.hour_of_day).padStart(2, '0')} 时）` : '—';
    document.getElementById('kpiIdle').textContent = idleZones.size;
    document.getElementById('kpiAvg').textContent = avg.toFixed(4);
}

/* ---------------- 图表 ---------------- */

function renderImbalance(rows) {
    const top = topByZone(rows, 15).slice().reverse();
    CHARTS.imbalance?.setOption({
        tooltip: {
            trigger: 'axis',
            formatter: p => {
                const r = top[p[0].dataIndex];
                const occ = OCC[r.zone_id] || {};
                return `${r.zone_id} 区<br>失衡指数 ${r.imbalance.toFixed(4)}<br>`
                     + `${String(r.hour_of_day).padStart(2, '0')} 时<br>`
                     + `需求份额 ${r.demand.toFixed(4)}　运力份额 ${r.supply.toFixed(4)}<br>`
                     + `充电桩 ${occ.charge_count ?? '—'} 个`;
            },
        },
        grid: { left: 60, right: 30, top: 20, bottom: 40 },
        xAxis: { type: 'value', name: '失衡指数 I', nameTextStyle: { color: '#94a3b8' },
                 axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,.15)' } } },
        yAxis: { type: 'category', data: top.map(r => r.zone_id),
                 axisLabel: { color: '#cbd5e1' }, axisLine: { lineStyle: { color: '#475569' } } },
        series: [{
            type: 'bar',
            data: top.map(r => ({
                value: r.imbalance,
                itemStyle: { color: r.imbalance > 0 ? '#ef4444' : '#3b82f6', borderRadius: [0, 4, 4, 0] },
            })),
            barMaxWidth: 18,
            label: { show: true, position: 'right', color: '#e2e8f0', formatter: p => p.value.toFixed(4) },
        }],
    });
}

function renderScatter(rows) {
    const seen = new Set();
    const pts = [];
    for (const r of rows) {
        if (seen.has(r.zone_id)) continue;
        seen.add(r.zone_id);
        const occ = OCC[r.zone_id] || {};
        pts.push({
            value: [occ.avg_occupancy ?? 0, r.imbalance, r.zone_id, occ.charge_count ?? 0],
            itemStyle: { color: r.imbalance > 0 ? '#ef4444' : '#3b82f6', opacity: .72 },
        });
    }
    CHARTS.scatter?.setOption({
        tooltip: {
            formatter: p => `${p.value[2]} 区<br>平均占用率 ${(p.value[0] * 100).toFixed(1)}%`
                         + `<br>失衡指数 ${p.value[1].toFixed(4)}<br>充电桩 ${p.value[3]} 个`,
        },
        grid: { left: 60, right: 24, top: 24, bottom: 46 },
        xAxis: { type: 'value', name: '平均占用率', nameTextStyle: { color: '#94a3b8' },
                 axisLabel: { color: '#94a3b8', formatter: v => (v * 100).toFixed(0) + '%' },
                 splitLine: { lineStyle: { color: 'rgba(148,163,184,.15)' } } },
        yAxis: { type: 'value', name: '失衡指数', nameTextStyle: { color: '#94a3b8' },
                 axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,.15)' } } },
        series: [{ type: 'scatter', data: pts, symbolSize: d => 6 + Math.sqrt(d[3]) * 0.7 }],
    });
}

function renderHourDist(rows) {
    const byHour = Array.from({ length: 24 }, () => ({ pos: 0, neg: 0 }));
    rows.forEach(r => {
        const h = r.hour_of_day;
        if (h < 0 || h > 23) return;
        if (r.imbalance > 0) byHour[h].pos++;
        else byHour[h].neg++;
    });
    CHARTS.hourDist?.setOption({
        tooltip: { trigger: 'axis' },
        legend: { textStyle: { color: '#cbd5e1' } },
        grid: { left: 50, right: 20, top: 34, bottom: 40 },
        xAxis: { type: 'category', data: Array.from({ length: 24 }, (_, i) => i),
                 axisLabel: { color: '#94a3b8', interval: 1 }, axisLine: { lineStyle: { color: '#475569' } } },
        yAxis: { type: 'value', name: '记录数', nameTextStyle: { color: '#94a3b8' },
                 axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(148,163,184,.15)' } } },
        series: [
            { name: '供不应求', type: 'bar', stack: 'h', data: byHour.map(x => x.pos), itemStyle: { color: '#ef4444' } },
            { name: '运力闲置', type: 'bar', stack: 'h', data: byHour.map(x => -x.neg), itemStyle: { color: '#3b82f6' } },
        ],
    });
}

/* ---------------- 导出 ---------------- */

function exportCSV() {
    const rows = getFilters();
    const head = ['zone_id', 'hour_of_day', 'imbalance', 'demand_share', 'supply_share'];
    const body = rows.map(r => [r.zone_id, r.hour_of_day, r.imbalance, r.demand, r.supply].join(','));
    const blob = new Blob(['﻿' + [head.join(','), ...body].join('\n')],
                          { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = '供需失衡指数_筛选结果.csv';
    a.click();
    URL.revokeObjectURL(a.href);
}

/* ---------------- 初始化 ---------------- */

function initCharts() {
    CHARTS.imbalance = echarts.init(document.getElementById('chartImbalance'));
    CHARTS.scatter  = echarts.init(document.getElementById('chartScatter'));
    CHARTS.hourDist = echarts.init(document.getElementById('chartHourDist'));
    window.addEventListener('resize', () => Object.values(CHARTS).forEach(c => c && c.resize()));
}

function fillZoneSelect() {
    const sel = document.getElementById('zoneSelect');
    const zones = [...new Set(ZONES.map(r => r.zone_id))].sort((a, b) => a - b);
    zones.forEach(z => {
        const o = document.createElement('option');
        o.value = z; o.textContent = `${z} 区`;
        sel.appendChild(o);
    });
}

function refresh() {
    const rows = getFilters();
    renderKPI(rows);
    renderImbalance(rows);
    renderScatter(rows);
    renderHourDist(rows);
}

document.addEventListener('DOMContentLoaded', async () => {
    initCharts();
    try {
        await loadData();
        fillZoneSelect();
        refresh();
        document.getElementById('btnQuery').addEventListener('click', refresh);
        document.getElementById('btnExport').addEventListener('click', exportCSV);
    } catch (e) {
        console.error('[page-zones] 数据加载失败', e);
        document.querySelector('.chart-tip').textContent = '数据加载失败：' + e.message;
    }
});
