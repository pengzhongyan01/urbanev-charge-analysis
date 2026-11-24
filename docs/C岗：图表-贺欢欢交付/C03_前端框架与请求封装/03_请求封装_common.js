/* 请求封装 · 缓存 · 降级 · 通用工具
 * 设计：切换真实接口只改 UEV.cfg.base，业务层（app.js）零改动
 *       接口不可用 → 直接读本地 data.js 兜底，保证离线演示不白屏
 */
(function (global) {
  const cfg = {
    base: null,            // 例：'http://localhost:8080/api/v1'；null = 纯离线
    timeout: 30000,
    retry: 2,
    cacheTTL: 5 * 60 * 1000 // 5 分钟
  };

  const cache = new Map();
  let cacheHits = 0;

  function hashKey(path, params) {
    return path + '?' + Object.keys(params || {}).sort()
      .map(k => k + '=' + encodeURIComponent(params[k])).join('&');
  }

  /** 带超时 + 重试的 fetch */
  function fetchWithTimeout(url, opt, attempt) {
    attempt = attempt || 0;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), cfg.timeout);
    return fetch(url, Object.assign({}, opt, { signal: ctrl.signal }))
      .then(r => { clearTimeout(timer); if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .catch(err => {
        clearTimeout(timer);
        if (attempt < cfg.retry) return fetchWithTimeout(url, opt, attempt + 1);
        throw err;
      });
  }

  /** 离线兜底：从内嵌数据取，路径 → 数据片段 */
  function fallback(path) {
    const D = global.UEV_DATA || {};
    const map = {
      '/kpi': D.kpi, '/zones': D.zones, '/zone-detail': D.zoneInfo,
      '/hourly': D.hourly, '/imbalance': D.imbalance, '/elasticity': D.elasticity,
      '/forecast': D.forecast, '/suggestion': D.expansion, '/dq': D.dq
    };
    return map[path] !== undefined ? map[path] : null;
  }

  const api = {
    cfg,
    get(path, params) {
      const key = hashKey(path, params);
      const hit = cache.get(key);
      if (hit && Date.now() - hit.t < cfg.cacheTTL) {
        cacheHits++; global.UEV_updateCacheHint && global.UEV_updateCacheHint(true);
        return new Promise(res => setTimeout(() => res(hit.v), 0));
      }
      const offline = new Promise(res => {
        const v = fallback(path);
        cache.set(key, { v, t: Date.now() });
        global.UEV_updateCacheHint && global.UEV_updateCacheHint(false);
        setTimeout(() => res(v), 0);
      });
      if (!cfg.base) return offline;
      const qs = Object.keys(params || {}).length
        ? '?' + Object.keys(params).map(k => k + '=' + encodeURIComponent(params[k])).join('&') : '';
      return fetchWithTimeout(cfg.base + path + qs, { headers: { Accept: 'application/json' } })
        .then(res => {
          const v = (res && res.code === 0 && 'data' in res) ? res.data : res;
          cache.set(key, { v, t: Date.now() });
          global.UEV_updateCacheHint && global.UEV_updateCacheHint(false);
          return v;
        })
        .catch(err => {
          console.warn('[api] 接口不可用，降级本地样例：', path, err.message);
          const v = fallback(path);
          cache.set(key, { v, t: Date.now() });
          return v;
        });
    },
    clear() { cache.clear(); cacheHits = 0; },
    get hits() { return cacheHits; }
  };

  const fmt = {
    pct: v => (v === null || v === undefined || isNaN(v)) ? '--' : (v * 100).toFixed(1) + '%',
    num: v => (v === null || v === undefined || isNaN(v)) ? '--'
      : (v >= 1e8 ? (v / 1e8).toFixed(2) + ' 亿' : (v >= 1e4 ? (v / 1e4).toFixed(1) + ' 万' : Math.round(v))),
    int: v => (v === null || v === undefined || isNaN(v)) ? '--' : Math.round(v).toLocaleString(),
    kwh: v => (v === null || v === undefined || isNaN(v)) ? '--' : v.toFixed(2) + ' kWh'
  };

  /** 导出 CSV：UTF-8 BOM，防 Excel 打开中文乱码 */
  function toCSV(header, rows) {
    const esc = s => {
      s = (s === null || s === undefined) ? '' : String(s);
      return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    };
    const lines = [header.map(esc).join(',')].concat(rows.map(r => r.map(esc).join(',')));
    return '\ufeff' + lines.join('\r\n');
  }

  function downloadCSV(filename, header, rows) {
    const blob = new Blob([toCSV(header, rows)], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 100);
  }

  function toast(msg, type) {
    const el = document.createElement('div');
    el.textContent = msg;
    el.style.cssText = 'position:fixed;right:24px;bottom:26px;z-index:99;padding:9px 16px;' +
      'border-radius:6px;font-size:12px;background:' + (type === 'warn' ? '#3a1f12' : '#0f2a45') +
      ';border:1px solid ' + (type === 'warn' ? '#ff6b35' : '#00d4ff') + ';color:#e6f1ff;' +
      'box-shadow:0 4px 16px rgba(0,0,0,.4)';
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2200);
  }

  global.UEV = { api, fmt, toast, downloadCSV, toCSV };
})(window);
