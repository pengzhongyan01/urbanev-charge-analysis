/* ==============================================================================
 * common.js —— 前端公共工具（骨架模板）
 *
 * 维护人：C（贺欢欢）　|　骨架由 A（彭忠燕）提供，2026-11-19
 *
 * 内容：
 *   1. API 请求封装（统一处理 code / 错误）
 *   2. ECharts 主题（深色，答辩投影友好）
 *   3. 格式化工具
 *   4. 时钟
 * ============================================================================== */

/* ---------------- 1. API 请求封装 ---------------- */

/**
 * 后端地址：同源部署时走相对路径，走 Nginx 代理
 * 独立调试时改成 http://localhost:8080/api
 */
const API_BASE = (window.__API_BASE__ || '') + '/api';

/**
 * 通用 GET 请求
 * @param {string} path   接口路径，如 '/dashboard/kpi'
 * @param {object} params 查询参数
 * @returns {Promise<any>} data 字段
 */
async function apiGet(path, params = {}) {
    const url = new URL(API_BASE + path, window.location.origin);
    Object.keys(params).forEach(k => {
        if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
            url.searchParams.append(k, params[k]);
        }
    });

    const res = await fetch(url.toString(), { method: 'GET' });
    if (!res.ok) {
        throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }

    const json = await res.json();
    if (json.code !== 200) {
        throw new Error(json.message || '请求失败');
    }
    return json.data;
}

/**
 * 通用 POST 请求
 */
async function apiPost(path, body) {
    const res = await fetch(API_BASE + path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body || {})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    if (json.code !== 200) throw new Error(json.message || '请求失败');
    return json.data;
}

/**
 * 带错误提示的查询包装
 * 出错时在控制台打印并在页面上给出提示，不让页面白屏
 */
async function safeQuery(fn, errTarget) {
    try {
        return await fn();
    } catch (e) {
        console.error('[请求失败]', e);
        if (errTarget) {
            const el = document.querySelector(errTarget);
            if (el) {
                el.innerHTML =
                    `<div style="color:#ef4444;font-size:13px;padding:20px;text-align:center">
                        ⚠ 数据加载失败：${e.message}<br>
                        <span style="color:#8fa8c8;font-size:11px">
                        请确认后端已启动（bash scripts/start_all.sh）
                        </span></div>`;
            }
        }
        return null;
    }
}

/* ---------------- 2. ECharts 主题 ---------------- */

/** 深色主题配色，与 CSS 变量保持一致 */
const CHART_COLORS = [
    '#00d4ff', '#ff6b35', '#22c55e', '#a78bfa',
    '#fbbf24', '#f472b6', '#38bdf8', '#fb923c',
    '#4ade80', '#c084fc', '#facc15', '#f87171'
];

/** 统一的 ECharts 基础配置 */
function baseOption(overrides = {}) {
    return Object.assign({
        textStyle: {
            fontFamily: '"Microsoft YaHei", "PingFang SC", sans-serif',
            color: '#e8f1ff'
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(10,22,40,.95)',
            borderColor: '#1e3a5f',
            borderWidth: 1,
            textStyle: { color: '#e8f1ff', fontSize: 12 },
            axisPointer: { type: 'shadow' }
        },
        legend: {
            textStyle: { color: '#8fa8c8', fontSize: 11 },
            itemWidth: 14, itemHeight: 9
        },
        grid: { left: 48, right: 24, top: 34, bottom: 34 },
        animationDuration: 600
    }, overrides);
}

/** 初始化图表并绑定 resize 自适应 */
function initChart(domId, option) {
    const dom = document.getElementById(domId);
    if (!dom) return null;
    const chart = echarts.init(dom);
    chart.setOption(option);
    window.addEventListener('resize', () => chart.resize());
    return chart;
}

/* ---------------- 3. 格式化工具 ---------------- */

/** 数字千分位 */
function formatNumber(n, digits = 0) {
    if (n === null || n === undefined || isNaN(n)) return '--';
    return Number(n).toLocaleString('zh-CN', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits
    });
}

/** 百分比 */
function formatPercent(n, digits = 1) {
    if (n === null || n === undefined || isNaN(n)) return '--';
    return (Number(n) * 100).toFixed(digits) + '%';
}

/** 大数字单位缩写：12345 → 1.2万 */
function formatCompact(n) {
    if (n === null || n === undefined || isNaN(n)) return '--';
    const v = Number(n);
    if (Math.abs(v) >= 1e8) return (v / 1e8).toFixed(2) + '亿';
    if (Math.abs(v) >= 1e4) return (v / 1e4).toFixed(2) + '万';
    return formatNumber(v);
}

/* ---------------- 4. 时钟 ---------------- */

function startClock() {
    const el = document.getElementById('clock');
    if (!el) return;
    const tick = () => {
        const d = new Date();
        const p = n => String(n).padStart(2, '0');
        el.textContent = `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ` +
                         `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
    };
    tick();
    setInterval(tick, 1000);
}

/* ---------------- 5. 系统状态指示 ---------------- */

async function checkStatus() {
    const el = document.getElementById('sysStatus');
    if (!el) return;
    try {
        const data = await apiGet('/health');
        const comps = data.components || {};
        const ok = comps.mysql === 'UP' && comps.redis === 'UP';
        el.textContent = ok ? '● 系统正常' : '● 部分组件异常';
        el.className = ok ? 'status' : 'status down';
    } catch (e) {
        el.textContent = '● 后端未连接';
        el.className = 'status down';
    }
}
