/* C07 · 导出实现（CSV，UTF-8 BOM，纯前端拼装，不触发接口请求）
 * 用法：UEV.downloadCSV('ads_zone_occupancy_2022-09-01_2023-02-28.csv', header, rows)
 */
function toCSV(header, rows) {
  const esc = s => {
    s = (s === null || s === undefined) ? '' : String(s);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const lines = [header.map(esc).join(',')].concat(rows.map(r => r.map(esc).join(',')));
  return '\ufeff' + lines.join('\r\n');   // BOM：防 Excel 中文乱码
}

function downloadCSV(filename, header, rows) {
  const blob = new Blob([toCSV(header, rows)], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a); a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 100);
}

/* ── 图表 PNG 导出（C07 第③类导出）────────────────────────────
 * ECharts 实例直接取画布，前端拼装、不触发接口请求。
 * 目标宽度 ≈1920（按图表宽度反算倍率 1.5~3），backgroundColor 用看板深色底避免透明底。
 */
function downloadChartPNG(chart, filename, opts) {
  opts = opts || {};
  if (!chart || typeof chart.getDataURL !== 'function') return false;
  // 目标宽度 1920px：按图表实际宽度反算倍率（1.5~3 倍之间）
  var w = (typeof chart.getWidth === 'function' && chart.getWidth()) || 960;
  var ratio = opts.pixelRatio || Math.min(3, Math.max(1.5, 1920 / w));
  var url = chart.getDataURL({
    type: 'png',
    pixelRatio: ratio,
    backgroundColor: opts.background || '#0b1a2f'
  });
  var a = document.createElement('a');
  a.href = url; a.download = filename;
  document.body.appendChild(a); a.click();
  setTimeout(function () { a.remove(); }, 100);
  return true;
}

/* 命名规范：表名 + 筛选摘要 + 时间戳
 * 例：ads_imbalance_index_2022-09-01_2023-02-28.csv
 */
