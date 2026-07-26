(function() {
  const { h, ref, computed, watch, onMounted, onBeforeUnmount } = window.__EXT_VUE__;

const MAX_TOKENS = 100_000_000;

function formatTokens(n) {
  if (!n) return '0';
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return String(n);
}

window.__DASHBOARD_FLOATING__ = {
  name: 'DashboardFloating',
  props: { api: Object, settings: Object },
  setup(props) {
    // 从 window.__EXT_VUE__ 实时读取（非 IIFE 闭包），兼容 HMR / contextIsolation
    const V = window.__EXT_VUE__;
    if (!V || typeof V.ref !== 'function') {
      console.error('[Dashboard] window.__EXT_VUE__ 异常:', V);
      return () => null;
    }
    const { ref, computed, watch, onMounted, onBeforeUnmount } = V;
    const expanded = ref(false);
    const metrics = ref(null);
    const pos = ref({ x: -1, y: -1 });
    const dragging = ref(false);
    const dragOffset = ref({ x: 0, y: 0 });
    const wasDragged = ref(false);
    let pollTimer = null;

    // 读 localStorage 恢复位置
    try {
      const saved = localStorage.getItem('dashboard-position');
      if (saved) pos.value = JSON.parse(saved);
    } catch (e) { /* ignore */ }

    // 默认位置：右下角
    const x = computed(() => pos.value.x !== -1 ? pos.value.x : window.innerWidth - 60);
    const y = computed(() => pos.value.y !== -1 ? pos.value.y : window.innerHeight - 160);

    const pct = computed(() => {
      const t = metrics.value?.total_prompt_tokens || 0;
      return Math.min(100, Math.round((t / MAX_TOKENS) * 100));
    });

    const barColor = computed(() => pct.value > 80 ? '#f44336' : pct.value > 50 ? '#ff9800' : '#4caf50');

    const hitColor = computed(() => {
      const r = metrics.value?.last_hit_rate || 0;
      return r >= 0.6 ? '#4caf50' : r >= 0.3 ? '#ff9800' : '#f44336';
    });

    async function fetchMetrics() {
      const conv = props.api?.getCurrentConversation?.();
      if (!conv?.id) return;
      try {
        const resp = await fetch(`/api/ext/dashboard/${conv.id}/metrics`);
        const json = await resp.json();
        if (json.code === 0) metrics.value = json.data;
      } catch (e) { /* ignore */ }
    }

    function onPointerDown(e) {
      if (expanded.value) return;
      dragging.value = true;
      wasDragged.value = false;
      dragOffset.value = {
        x: e.clientX - x.value,
        y: e.clientY - y.value,
      };
      e.preventDefault();
    }

    function onPointerMove(e) {
      if (!dragging.value) return;
      const dx = e.clientX - dragOffset.value.x;
      const dy = e.clientY - dragOffset.value.y;
      if (Math.abs(dx - x.value) > 2 || Math.abs(dy - y.value) > 2) {
        wasDragged.value = true;
      }
      pos.value = { x: dx, y: dy };
    }

    function onPointerUp() {
      if (dragging.value) {
        try { localStorage.setItem('dashboard-position', JSON.stringify(pos.value)); } catch(e){}
      }
      dragging.value = false;
    }

    function onBtnClick(e) {
      if (wasDragged.value) return;
      e.stopPropagation();
      expanded.value = !expanded.value;
    }

    // 展开/收起时统一管理定时器（受 auto-refresh 控制）
    watch(expanded, (val) => {
      if (val) {
        fetchMetrics();
        const autoRefresh = props.settings?.features?.['auto-refresh'] !== false;
        if (autoRefresh) {
          pollTimer = setInterval(fetchMetrics, 3000);
        }
      } else {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    });

    function onBackdropClick() {
      expanded.value = false;
    }

    onMounted(() => {
      document.addEventListener('pointermove', onPointerMove);
      document.addEventListener('pointerup', onPointerUp);
    });

    onBeforeUnmount(() => {
      document.removeEventListener('pointermove', onPointerMove);
      document.removeEventListener('pointerup', onPointerUp);
      clearInterval(pollTimer);
    });

    const btnStyle = {
      position: 'fixed', left: '0px', top: '0px', transform: 'translate(-50%, -50%)',
      width: '40px', height: '40px', borderRadius: '50%',
      background: '#4a90d9', color: '#fff',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      cursor: dragging.value ? 'grabbing' : 'grab',
      fontSize: '18px', zIndex: 10000,
      boxShadow: '0 2px 8px rgba(0,0,0,0.25)',
      userSelect: 'none', touchAction: 'none',
    };

    const panelStyle = {
      position: 'fixed', left: '0px', top: '0px',
      width: '180px', height: '400px', borderRadius: '12px',
      background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(12px)',
      boxShadow: '0 4px 24px rgba(0,0,0,0.18)',
      zIndex: 9999, padding: '14px 12px',
      display: 'flex', flexDirection: 'column', gap: '8px',
      fontSize: '12px', color: '#333', overflow: 'hidden',
    };

    const sectionTitle = { fontWeight: 600, fontSize: '13px', color: '#444' };
    const row = { display: 'flex', justifyContent: 'space-between', alignItems: 'center' };
    const divider = { borderTop: '1px solid #eee', margin: '2px 0' };

    return () => {
      const feat = props.settings?.features || {};
      const btnLeft = x.value + 'px';
      const btnTop = y.value + 'px';

      const btn = h('div', {
        onPointerdown: onPointerDown,
        onClick: onBtnClick,
        style: { ...btnStyle, left: btnLeft, top: btnTop },
      }, '📊');

      if (!expanded.value) return btn;

      // 面板位于圆纽左上方
      const px = x.value + 'px';
      const py = y.value + 'px';
      const m = metrics.value || {};

      // 面板位于按钮左上方，clamp 防止超出屏幕
      const panelLeft = Math.max(10, x.value - 200);
      const panelTop  = Math.max(10, y.value - 420);

      const panel = h('div', { style: { ...panelStyle, right: 'auto', bottom: 'auto',
                                        left: panelLeft + 'px',
                                        top: panelTop + 'px',
                                        transform: 'none' } }, [
        // 上下文窗口（受 show-context-usage 控制）
        ...(feat['show-context-usage'] !== false ? [
        h('div', { style: sectionTitle }, '📊 上下文窗口'),
        h('div', { style: row }, [
          h('span', null, `${formatTokens(m.total_prompt_tokens)} / 100M`),
          h('span', { style: { color: barColor.value, fontWeight: 600 } }, `${pct.value}%`),
        ]),
        h('div', { style: { height:'6px', borderRadius:'3px', background:'#eee', overflow:'hidden' } }, [
          h('div', { style: { width:pct.value+'%', height:'100%', borderRadius:'3px',
                              background:barColor.value, transition:'width 0.3s' } }),
        ]),
        ] : []),

        ...(feat['show-context-usage'] !== false && feat['session-metrics'] !== false ? [
        h('div', { style: divider }),
        ] : []),

        // 会话指标（受 session-metrics group 控制）
        ...(feat['session-metrics'] !== false ? [
        ...(feat['session-metrics.hit-rate'] !== false || feat['session-metrics.request-count'] !== false || feat['session-metrics.completion-tokens'] !== false ? [
        h('div', { style: sectionTitle }, '📈 会话指标'),
        ] : []),
        ...(feat['session-metrics.hit-rate'] !== false ? [
        h('div', { style: row }, [
          h('span', null, '命中率'),
          h('span', { style: { color: hitColor.value, fontWeight: 600 } },
            `${Math.round((m.last_hit_rate || 0) * 100)}%`),
        ]),
        ] : []),
        ...(feat['session-metrics.request-count'] !== false ? [
        h('div', { style: row }, [
          h('span', null, '请求次数'),
          h('span', { style: { fontWeight: 600 } }, String(m.request_count || 0)),
        ]),
        ] : []),
        ...(feat['session-metrics.completion-tokens'] !== false ? [
        h('div', { style: row }, [
          h('span', null, '累计 AI token'),
          h('span', { style: { fontWeight: 600 } }, formatTokens(m.total_completion_tokens)),
        ]),
        ] : []),
        ] : []),
      ]);

      // backdrop 点击收起
      const backdrop = h('div', {
        onClick: onBackdropClick,
        style: { position:'fixed', inset:0, zIndex:9998 },
      });

      return h('div', null, [backdrop, panel, btn]);
    };
  },
};
})();
