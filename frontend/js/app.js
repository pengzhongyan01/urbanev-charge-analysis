/* 控制层：筛选 → 取数 → 渲染 10 个核心图表
 * 每个 render*() 只做「取数 + setOption」，DOM 结构在 index.html 里固定
 */
(function () {
  const C = { cyan: '#00d4ff', orange: '#ff6b35', green: '#22c55e', yellow: '#ffc107', purple: '#8b5cf6', muted: '#8fa8c8' };
  const BG = '#12253f';

  const STATE = {
    filters: { start: '2022-09-01', end: '2023-02-28', zone: 'all', hour: 'all', pri: 'all' },
    data: {},
    charts: {}
  };

  /* ---------------- 主题 ---------------- */
  function baseOption(extra) {
    return Object.assign({
      backgroundColor: 'transparent',
      textStyle: { color: '#e6f1ff', fontFamily: 'Microsoft YaHei' },
      grid: { left: 46, right: 24, top: 30, bottom: 34, containLabel: true },
      tooltip: {
        trigger: 'axis', backgroundColor: '#0b1a2f', borderColor: '#2f5b86',
        textStyle: { color: '#e6f1ff', fontSize: 11 }, axisPointer: { type: 'shadow' }
      },
      legend: { right: 10, top: 4, textStyle: { color: C.muted, fontSize: 11 }, itemWidth: 12, itemHeight: 8 }
    }, extra || {});
  }
  function axisX(data, name) {
    return { type: 'category', data: data, name: name || '', axisLine: { lineStyle: { color: '#2f5b86' } },
      axisLabel: { color: C.muted, fontSize: 10 }, splitLine: { show: false } };
  }
  function axisY(name, fmt) {
    return { type: 'value', name: name || '', axisLine: { show: false }, splitLine: { lineStyle: { color: '#1e3a5f' } },
      axisLabel: { color: C.muted, fontSize: 10, formatter: fmt || null } };
  }
  function init(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    const c = echarts.init(el, null, { renderer: 'canvas' });
    STATE.charts[id] = c;
    return c;
  }
  function get(id) { return STATE.charts[id] || init(id); }

  /* ---------------- 取数 ---------------- */
  async function loadAll() {
    const f = STATE.filters;
    const [kpi, zones, zoneInfo, hourly, imbalance, elasticity, forecast, expansion, dq] = await Promise.all([
      UEV.api.get('/kpi', { start: f.start, end: f.end }),
      UEV.api.get('/zones', { start: f.start, end: f.end, zone: f.zone }),
      UEV.api.get('/zone-detail', {}),
      UEV.api.get('/hourly', { hour: f.hour }),
      UEV.api.get('/imbalance', { hour: f.hour }),
      UEV.api.get('/elasticity', {}),
      UEV.api.get('/forecast', { zone: f.zone }),
      UEV.api.get('/suggestion', { pri: f.pri }),
      UEV.api.get('/dq', {})
    ]);
    STATE.data = { kpi, zones, zoneInfo, hourly, imbalance, elasticity, forecast, expansion, dq };
    renderAll();
  }

  /* ---------------- 渲染 ---------------- */
  function renderAll() {
    fillZoneOptions();
    renderKpi();
    renderHourly();
    renderDq();
    renderMap();
    renderZoneTop();
    renderImbalance();
    renderPrice();
    renderElastic();
    renderForecast();
    renderMape();
    renderExpansion();
    renderTables();
    Object.values(STATE.charts).forEach(c => c && c.resize());
  }

  function renderKpi() {
    const k = STATE.data.kpi || {};
    const cards = [
      { n: '覆盖分区数', v: UEV.fmt.int(k.station_count), u: '个交通分区', c: '' },
      { n: '充电桩数', v: UEV.fmt.int(k.pile_count), u: '个', c: '' },
      { n: '平均占用率', v: UEV.fmt.pct(k.avg_occupancy), u: '全时段均值', c: 'orange' },
      { n: '总充电量', v: UEV.fmt.num(k.total_volume), u: 'kWh', c: 'green' },
      { n: '持续紧张分区', v: UEV.fmt.int(k.persistent_imbalance_zones ?? k.imbalance_zones), u: '失衡时段占一半以上', c: 'orange' }
    ];
    document.getElementById('kpiRow').innerHTML = cards.map(c =>
      `<div class="kpi ${c.c}"><div class="k-name">${c.n}</div><div class="k-val">${c.v}</div><div class="k-unit">${c.u}</div></div>`
    ).join('');
  }

  function renderHourly() {
    const c = get('chartHourly'); if (!c) return;
    const d = STATE.data.hourly || [];
    c.setOption(baseOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { data: ['平均占用率', '需求强度', '供需缺口'], top: 2 },
      grid: { left: 52, right: 56, top: 34, bottom: 34, containLabel: true },
      xAxis: axisX(d.map(x => x.h + '时')),
      yAxis: [
        axisY('占用率', v => Math.round(v * 100) + '%'),
        axisY('缺口', v => v.toFixed(2))
      ],
      series: [
        { name: '平均占用率', type: 'line', smooth: true, symbolSize: 5, yAxisIndex: 0,
          data: d.map(x => x.occ), lineStyle: { width: 2.4, color: C.cyan }, itemStyle: { color: C.cyan },
          areaStyle: { color: 'rgba(0,212,255,.14)' } },
        { name: '需求强度', type: 'line', smooth: true, symbolSize: 4, yAxisIndex: 0,
          data: d.map(x => x.demand), lineStyle: { width: 2, color: C.green }, itemStyle: { color: C.green } },
        { name: '供需缺口', type: 'bar', yAxisIndex: 1, barWidth: '55%',
          data: d.map(x => x.gap), itemStyle: { color: 'rgba(255,107,53,.42)' } }
      ]
    }), true);
  }

  function renderDq() {
    const c = get('chartDq'); if (!c) return;
    const q = STATE.data.dq || {};
    const items = [
      ['有效行', q.valid_rows, C.green], ['时间非法', q.time_invalid, C.orange],
      ['数值为空', q.value_nan_before, C.yellow], ['超出范围', q.out_of_range, C.orange],
      ['重复删除', q.dup_removed, C.purple], ['清洗后空值', q.nan_after_clean, C.muted]
    ];
    c.setOption(baseOption({
      grid: { left: 52, right: 20, top: 36, bottom: 40, containLabel: true },
      xAxis: Object.assign(axisX(items.map(i => i[0])), {
        axisLabel: { color: C.muted, fontSize: 9, rotate: 16, interval: 0 }
      }),
      yAxis: axisY('行数', v => v >= 10000 ? (v / 10000).toFixed(0) + '万' : v),
      series: [{
        type: 'bar', barWidth: '46%',
        data: items.map(i => ({ value: i[1], itemStyle: { color: i[2] } })),
        label: { show: true, position: 'top', color: '#e6f1ff', fontSize: 10,
          formatter: p => p.value >= 10000 ? (p.value / 10000).toFixed(0) + '万' : p.value }
      }],
      legend: { show: false }
    }), true);
  }

  function renderMap() {
    const c = get('chartMap'); if (!c) return;
    const geo = window.UEV_GEO;
    if (geo && !echarts.getMap('shenzhen')) {
      const feats = geo.features.map(f => ({
        type: 'Feature',
        properties: { name: f.properties.name },
        geometry: {
          type: 'Polygon',
          coordinates: f.geometry.type === 'MultiPolygon' ? f.geometry.coordinates.flat() : f.geometry.coordinates
        }
      }));
      echarts.registerMap('shenzhen', { type: 'FeatureCollection', features: feats });
    }
    const info = STATE.data.zoneInfo || [];
    const occMap = {};
    (STATE.data.zones || []).forEach(z => { occMap[z.id] = z; });
    const sel = STATE.filters.zone;
    const pts = info.map(z => {
      const o = occMap[z.id];
      const val = o ? o.occ : null;
      return {
        name: String(z.id), value: [z.lon, z.lat, val === null ? -1 : val],
        piles: z.cc,
        itemStyle: { color: val === null ? '#2c4666' : (val > 0.7 ? C.orange : val > 0.4 ? C.cyan : C.green) },
        symbolSize: val === null ? 5 : 6 + val * 12,
        emphasis: { scale: 1.6, itemStyle: { borderColor: '#fff', borderWidth: 1 } }
      };
    });
    const focus = sel !== 'all' ? pts.filter(p => p.name === String(sel)) : [];
    c.setOption(baseOption({
      tooltip: {
        trigger: 'item', backgroundColor: '#0b1a2f', borderColor: '#2f5b86',
        formatter: p => {
          const v = p.value[2];
          return `<b>交通分区 ${p.name}</b><br/>平均占用率：${v < 0 ? '样例库未覆盖' : (v * 100).toFixed(1) + '%'}` +
            `<br/>充电桩：${p.data.piles} 个`;
        }
      },
      geo: {
        map: 'shenzhen', roam: true, zoom: 1.05, label: { show: true, color: '#9fc4e8', fontSize: 10 },
        itemStyle: { areaColor: '#0f2038', borderColor: '#2f5b86', borderWidth: 1 },
        emphasis: { itemStyle: { areaColor: '#16324f' }, label: { show: false } }
      },
      series: [
        { name: '分区散点', type: 'scatter', coordinateSystem: 'geo', data: pts, zlevel: 3 },
        { name: '当前分区', type: 'effectScatter', coordinateSystem: 'geo', data: focus,
          rippleEffect: { scale: 3, brushType: 'stroke' }, itemStyle: { color: '#fff' }, zlevel: 4 }
      ],
      legend: { show: true, data: ['分区散点'], top: 2 }
    }), true);
  }

  function renderZoneTop() {
    const c = get('chartZoneTop'); if (!c) return;
    const top = (STATE.data.zones || []).slice().sort((a, b) => b.occ - a.occ).slice(0, 20).reverse();
    c.setOption(baseOption({
      grid: { left: 54, right: 60, top: 26, bottom: 24, containLabel: true },
      xAxis: axisY('平均占用率', v => Math.round(v * 100) + '%'),
      yAxis: { type: 'category', data: top.map(z => String(z.id)), axisLine: { lineStyle: { color: '#2f5b86' } },
        axisLabel: { color: C.muted, fontSize: 10 } },
      series: [{ type: 'bar', barWidth: '62%', data: top.map(z => ({ value: z.occ,
        itemStyle: { color: z.occ > 0.7 ? C.orange : C.cyan } })),
        label: { show: true, position: 'right', color: '#e6f1ff', fontSize: 10,
          formatter: p => (p.value * 100).toFixed(1) + '%' } }],
      legend: { show: false }
    }), true);
  }

  function renderImbalance() {
    const c = get('chartImbalance'); if (!c) return;
    const rows = STATE.data.imbalance || [];
    const agg = {};
    rows.forEach(x => { (agg[x.h] = agg[x.h] || []).push(x.idx); });
    const hs = Object.keys(agg).map(Number).sort((a, b) => a - b);
    const vals = hs.map(h => agg[h].reduce((a, b) => a + b, 0) / agg[h].length);
    const max = Math.max.apply(null, vals);
    c.setOption(baseOption({
      grid: { left: 56, right: 24, top: 26, bottom: 30, containLabel: true },
      xAxis: axisX(hs.map(h => h + '时')),
      yAxis: axisY('平均失衡指数'),
      series: [{ type: 'bar', barWidth: '58%',
        data: vals.map(v => ({ value: v, itemStyle: { color: v === max ? C.orange : C.cyan } })),
        label: { show: true, position: 'top', color: '#e6f1ff', fontSize: 9,
          formatter: p => p.value >= max ? p.value.toFixed(3) : '' } }],
      legend: { show: false }
    }), true);
  }

  function renderPrice() {
    const c = get('chartPrice'); if (!c) return;
    const d = STATE.data.elasticity || [];
    c.setOption(baseOption({
      xAxis: axisX(d.map(x => x.h + '时')),
      yAxis: axisY('平均占用率', v => Math.round(v * 100) + '%'),
      legend: { data: ['TOU 分时电价区', 'FLAT 平段电价区'], top: 2 },
      series: [
        { name: 'TOU 分时电价区', type: 'line', smooth: true, data: d.map(x => x.occTOU),
          lineStyle: { width: 2.4, color: C.cyan }, itemStyle: { color: C.cyan } },
        { name: 'FLAT 平段电价区', type: 'line', smooth: true, data: d.map(x => x.occFLAT),
          lineStyle: { width: 2.4, color: C.yellow }, itemStyle: { color: C.yellow } }
      ]
    }), true);
  }

  function renderElastic() {
    const c = get('chartElastic'); if (!c) return;
    const d = STATE.data.elasticity || [];
    c.setOption(baseOption({
      tooltip: { trigger: 'item', formatter: p => `${p.seriesName}<br/>${p.value[2]}时<br/>价差 ${p.value[0].toFixed(2)} 元/kWh<br/>占用率 ${(p.value[1] * 100).toFixed(1)}%` },
      legend: { data: ['TOU 分区', 'FLAT 分区'], top: 2 },
      grid: { left: 56, right: 26, top: 34, bottom: 40, containLabel: true },
      xAxis: axisY('平均价差（元/kWh）'),
      yAxis: axisY('平均占用率', v => Math.round(v * 100) + '%'),
      series: [
        { name: 'TOU 分区', type: 'scatter', symbolSize: 10,
          data: d.map(x => ({ value: [x.gapTOU, x.occTOU, x.h] })), itemStyle: { color: C.cyan } },
        { name: 'FLAT 分区', type: 'scatter', symbolSize: 10,
          data: d.map(x => ({ value: [x.gapFLAT, x.occFLAT, x.h] })), itemStyle: { color: C.yellow } }
      ]
    }), true);
  }

  function renderForecast() {
    const c = get('chartForecast'); if (!c) return;
    const all = STATE.data.forecast || [];
    const sel = STATE.filters.zone;
    let rows, zid;
    if (sel !== 'all') { rows = all.filter(x => String(x.zone) === String(sel)); zid = sel; }
    else {
      const counts = {};
      all.forEach(x => { counts[x.zone] = (counts[x.zone] || 0) + 1; });
      zid = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
      rows = all.filter(x => String(x.zone) === String(zid));
    }
    rows = rows.sort((a, b) => (a.date > b.date ? 1 : -1));
    const t = document.getElementById('fcTitle');
    if (t) t.textContent = `需求预测曲线 · 分区 ${zid}（回测 ${rows.length} 天 · 逐日）`;
    c.setOption(baseOption({
      xAxis: axisX(rows.map(x => String(x.date).slice(5))),
      yAxis: axisY('充电电量 kWh'),
      legend: { data: ['实际电量', '预测电量'], top: 2 },
      series: [
        { name: '实际电量', type: 'line', smooth: true, data: rows.map(x => x.act),
          lineStyle: { width: 2.4, color: C.cyan }, itemStyle: { color: C.cyan } },
        { name: '预测电量', type: 'line', smooth: true, data: rows.map(x => x.pred),
          lineStyle: { width: 2, color: C.orange, type: 'dashed' }, itemStyle: { color: C.orange } }
      ]
    }), true);
  }

  function renderMape() {
    const c = get('chartMape'); if (!c) return;
    const d = STATE.data.forecast || [];
    const m = d.map(x => x.mape);                       // 数据已是百分数（0~60）
    const max = Math.max.apply(null, m.concat([1]));
    const bins = 16, w = max / bins, hist = new Array(bins).fill(0);
    m.forEach(v => { hist[Math.min(bins - 1, Math.floor(v / w))]++; });
    const mean = m.reduce((a, b) => a + b, 0) / (m.length || 1);
    c.setOption(baseOption({
      xAxis: axisX(hist.map((_, i) => (i * w).toFixed(1) + '~')),
      yAxis: axisY('样本数'),
      series: [{ type: 'bar', barWidth: '82%', data: hist, itemStyle: { color: C.cyan, opacity: .82 },
        markLine: { silent: true, symbol: 'none', lineStyle: { color: C.orange, width: 2, type: 'dashed' },
          label: { color: C.orange, fontSize: 10, formatter: '均值 ' + mean.toFixed(1) + '%' },
          data: [{ xAxis: Math.min(bins - 1, Math.floor(mean / w)) }] } }],
      legend: { show: false }
    }), true);
  }

  function renderExpansion() {
    const c = get('chartExpansion'); if (!c) return;
    let rows = STATE.data.expansion || [];
    if (STATE.filters.pri !== 'all') rows = rows.filter(x => String(x.pri) === String(STATE.filters.pri));
    // 只画「真需要加桩」的分区，按建议新增量排序；筛成 P3（不加桩）时退化为按现有桩数排序
    rows = rows.filter(x => x.add > 0).sort((a, b) => b.add - a.add).slice(0, 15).reverse();
    if (!rows.length) rows = (STATE.data.expansion || []).filter(x => x.pri === 3)
      .sort((a, b) => b.cur - a.cur).slice(0, 15).reverse();
    c.setOption(baseOption({
      grid: { left: 54, right: 56, top: 34, bottom: 24, containLabel: true },
      legend: { data: ['现有桩数', '建议新增'], top: 2 },
      xAxis: axisY('桩数'),
      yAxis: { type: 'category', data: rows.map(x => String(x.zone)), axisLine: { lineStyle: { color: '#2f5b86' } },
        axisLabel: { color: C.muted, fontSize: 10 } },
      series: [
        { name: '现有桩数', type: 'bar', barWidth: '36%', barGap: '10%',
          data: rows.map(x => x.cur), itemStyle: { color: '#2f5b86' } },
        { name: '建议新增', type: 'bar', barWidth: '36%',
          data: rows.map(x => x.add), itemStyle: { color: C.orange } }
      ]
    }), true);
  }

  /* ---------------- 表格 ---------------- */
  function renderTables() {
    const h = STATE.data.hourly || [];
    const th = ['小时', '平均占用率', '需求强度', '供给', '缺口'];
    document.getElementById('tblHour').innerHTML =
      `<thead><tr>${th.map(x => `<th>${x}</th>`).join('')}</tr></thead><tbody>` +
      h.map(x => `<tr><td>${x.h} 时</td><td>${UEV.fmt.pct(x.occ)}</td><td>${UEV.fmt.pct(x.demand)}</td>
        <td>${x.supply.toFixed(4)}</td><td>${x.gap.toFixed(3)}</td></tr>`).join('') + '</tbody>';

    let e = STATE.data.expansion || [];
    if (STATE.filters.pri !== 'all') e = e.filter(x => String(x.pri) === String(STATE.filters.pri));
    // P1 先、同档内按「新增/现有」比例排序，再按新增量；P3 只作调度参考放最后
    e = e.slice().sort((a, b) =>
      (a.pri - b.pri) || (b.add / (b.cur || 1) - a.add / (a.cur || 1)) || (b.add - a.add)).slice(0, 20);
    const th2 = ['分区', '优先级', '现有', '建议新增', '理由（每条按本区实测生成）'];
    document.getElementById('tblSuggest').innerHTML =
      `<thead><tr>${th2.map(x => `<th>${x}</th>`).join('')}</tr></thead><tbody>` +
      e.map(x => {
        const tag = String(x.type || '').split('-')[1] || '';
        const add = x.add > 0 ? '+' + x.add : '0（不加桩）';
        return `<tr><td>${x.zone}</td><td><b>P${x.pri}</b> <span style="color:#8fa8c8;font-size:12px">${tag}</span></td>
          <td>${x.cur}</td><td>${add}</td><td style="text-align:left">${x.reason}</td></tr>`;
      }).join('') + '</tbody>';

    const note = document.getElementById('tblSuggestNote') || (() => {
      const d = document.createElement('div');
      d.id = 'tblSuggestNote';
      d.style.cssText = 'margin-top:10px;color:#8fa8c8;font-size:12px;line-height:1.7';
      document.getElementById('tblSuggest').parentElement.after(d);
      return d;
    })();
    const ex = STATE.data.expansion || [];
    const n1 = ex.filter(x => x.pri === 1).length, n2 = ex.filter(x => x.pri === 2).length;
    const nd = ex.filter(x => x.add > 0).length, tot = ex.reduce((a, b) => a + b.add, 0);
    note.innerHTML = `口径：<b>需加桩 ${nd} 个分区</b>（P1 持续紧张 ${n1} 个 / P2 尖峰·高密度 ${n2} 个），合计 +${tot} 桩；
      其余不加桩（含峰值错配型与过剩区，改为错峰调度与引流）。<br>
      新增量算法：add = ⌈现有桩数 × 峰值占用率 ÷ 目标峰值⌉ − 现有桩数（P1 目标 0.75、P2 目标 0.85），
      所以每个区的增量由它自己的峰值决定，不是统一倍数。`;
  }

  /* ---------------- 筛选与导航 ---------------- */
  function getFilters() {
    return {
      start: document.getElementById('fStart').value,
      end: document.getElementById('fEnd').value,
      zone: document.getElementById('fZone').value,
      hour: document.getElementById('fHour').value,
      pri: document.getElementById('fPri').value
    };
  }
  function validate(f) {
    if (!f.start || !f.end) { UEV.toast('请选择完整的时间范围', 'warn'); return false; }
    if (f.start > f.end) { UEV.toast('开始日期不能晚于结束日期', 'warn'); return false; }
    return true;
  }
  function syncUrl(f) {
    const q = Object.keys(f).map(k => k + '=' + encodeURIComponent(f[k])).join('&');
    try { history.replaceState(null, '', '?' + q); } catch (e) { /* file:// 下忽略 */ }
  }

  function bindEvents() {
    document.getElementById('tabs').addEventListener('click', e => {
      const b = e.target.closest('.tab'); if (!b) return;
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      b.classList.add('active');
      document.getElementById('' + b.dataset.page).classList.add('active');
      setTimeout(() => Object.values(STATE.charts).forEach(c => c && c.resize()), 60);
    });

    let timer = null;
    document.getElementById('btnApply').addEventListener('click', () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        const f = getFilters();
        if (!validate(f)) return;
        STATE.filters = f; syncUrl(f);
        UEV.api.clear();
        UEV.toast('筛选已应用：分区 ' + (f.zone === 'all' ? '全部' : f.zone) + ' / 小时 ' + (f.hour === 'all' ? '全时段' : f.hour));
        loadAll();
      }, 300);
    });

    document.getElementById('btnReset').addEventListener('click', () => {
      document.getElementById('fStart').value = '2022-09-01';
      document.getElementById('fEnd').value = '2023-02-28';
      document.getElementById('fZone').value = 'all';
      document.getElementById('fHour').value = 'all';
      document.getElementById('fPri').value = 'all';
      STATE.filters = getFilters(); syncUrl(STATE.filters);
      UEV.api.clear(); UEV.toast('已恢复默认筛选'); loadAll();
    });

    document.getElementById('btnExport').addEventListener('click', doExport);
    document.getElementById('btnExportPng').addEventListener('click', doExportPng);

    const fz = document.getElementById('fZone');
    const fh = document.getElementById('fHour');
    for (let i = 0; i < 24; i++) {
      const o = document.createElement('option'); o.value = i; o.textContent = i + ' 时'; fh.appendChild(o);
    }
  }

  /** 分区下拉依赖 zoneInfo，取数成功后再填充（只填一次） */
  function fillZoneOptions() {
    const fz = document.getElementById('fZone');
    if (!fz || fz.dataset.filled) return;
    (STATE.data.zoneInfo || []).forEach(z => {
      const o = document.createElement('option');
      o.value = z.id; o.textContent = `分区 ${z.id}（${z.cc} 桩）`;
      fz.appendChild(o);
    });
    fz.dataset.filled = '1';
  }

  /* ---------------- 导出（跟随当前筛选，纯前端拼装） ---------------- */
  function doExport() {
    const f = STATE.filters, D = STATE.data;
    const stamp = f.start + '_' + f.end;
    const activePage = (document.querySelector('.tab.active') || {}).dataset.page;

    if (activePage === 'p6') {
      UEV.downloadCSV(`ads_expansion_suggestion_${stamp}.csv`,
        ['zone_id', 'priority', 'zone_type', 'current_piles', 'add_piles', 'suggested_piles',
         'imbalance_share', 'avg_occupancy', 'max_occupancy', 'poi_per_pile', 'reason'],
        (D.expansion || []).map(x => [x.zone, x.pri, x.type, x.cur, x.add, x.sug,
                                      x.share, x.occ, x.peak, x.pp, x.reason]));
    } else if (activePage === 'p5') {
      UEV.downloadCSV(`ads_demand_forecast_${stamp}.csv`,
        ['zone_id', 'forecast_date', 'hour_of_day', 'predict_volume', 'actual_volume', 'mape'],
        (D.forecast || []).map(x => [x.zone, x.date, x.h, x.pred, x.act, x.mape]));
    } else if (activePage === 'p4') {
      UEV.downloadCSV(`ads_price_elasticity_${stamp}.csv`,
        ['hour_of_day', 'occ_TOU', 'occ_FLAT', 'gap_TOU', 'gap_FLAT'],
        (D.elasticity || []).map(x => [x.h, x.occTOU, x.occFLAT, x.gapTOU, x.gapFLAT]));
    } else if (activePage === 'p3') {
      UEV.downloadCSV(`ads_imbalance_index_${stamp}.csv`,
        ['zone_id', 'hour_of_day', 'demand', 'supply', 'imbalance'],
        (D.imbalance || []).map(x => [x.zone, x.h, x.demand, x.supply, x.idx]));
    } else if (activePage === 'p2') {
      UEV.downloadCSV(`ads_zone_occupancy_${stamp}.csv`,
        ['zone_id', 'longitude', 'latitude', 'avg_occupancy', 'max_occupancy', 'charge_count'],
        (D.zones || []).map(x => [x.id, x.lon, x.lat, x.occ, x.max, x.piles]));
    } else {
      UEV.downloadCSV(`ads_hourly_supply_demand_${stamp}.csv`,
        ['hour_of_day', 'avg_occupancy', 'avg_demand', 'avg_supply', 'gap'],
        (D.hourly || []).map(x => [x.h, x.occ, x.demand, x.supply, x.gap]));
    }
    UEV.toast('已导出当前筛选结果 CSV（UTF-8 BOM）');
  }

  /* 每页的主图：导 PNG 时取它，文件名带页名与筛选区间 */
  const PAGE_MAIN = {
    p1: ['chartHourly', '总览_24小时供需'],
    p2: ['chartMap', '分区地图_占用率分布'],
    p3: ['chartImbalance', '供需分析_失衡TOP15'],
    p4: ['chartPrice', '电价弹性_两类电价占用率'],
    p5: ['chartForecast', '需求预测_实际vs预测'],
    p6: ['chartExpansion', '布点建议_扩容TOP15']
  };

  function doExportPng() {
    const page = (document.querySelector('.tab.active') || {}).dataset.page || 'p1';
    const [cid, name] = PAGE_MAIN[page] || PAGE_MAIN.p1;
    const chat = STATE.charts[cid];
    const f = STATE.filters;
    if (!chat) { UEV.toast('当前页图表还没画出来，稍后再试'); return; }
    const ok = UEV.downloadChartPNG(chat, `${name}_${f.start}_${f.end}.png`);
    UEV.toast(ok ? '已导出当前图表 PNG（约 1920 宽）' : '这个图表暂不支持导出 PNG');
  }

  /* ---------------- 启动 ---------------- */
  function boot() {
    window.UEV_updateCacheHint = hit => {
      const el = document.getElementById('cacheHit');
      if (el) el.textContent = hit ? '缓存：命中（已复用上次结果）' : '缓存：本次新取';
    };
    STATE.filters = getFilters();
    bindEvents();
    loadAll();
    window.addEventListener('resize', () => Object.values(STATE.charts).forEach(c => c && c.resize()));
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  window.UEV_APP = { STATE, loadAll, renderAll, getFilters };
})();
