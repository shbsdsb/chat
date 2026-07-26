<template>
  <div
    class="drawer-panel"
    :class="{ open: !!store.detailExt, resizing: resizing }"
    :style="{ width: !!store.detailExt ? drawerWidth + 'px' : '0' }"
  >
    <div class="drawer-resize-handle" @mousedown.prevent="onResizeStart" />
    <div v-if="store.detailExt" class="drawer-body">
      <!-- 标题栏 -->
      <div class="detail-header">
        <div class="detail-title-row">
          <h3 class="detail-name">{{ store.detailExt.name || store.detailExt.id }}</h3>
          <button class="detail-close" @click="store.closeDetail()">✕</button>
        </div>
        <div class="detail-meta">
          <span class="detail-version">v{{ store.detailExt.version || '0.0.0' }}</span>
          <span v-if="manifest?.author" class="detail-author">by {{ manifest.author }}</span>
        </div>
      </div>

      <div v-if="detailLoading" class="detail-loading">加载中…</div>

      <template v-else>
        <!-- 基本信息 -->
        <section class="detail-section">
          <h4 class="detail-section-title">基本信息</h4>
          <div class="detail-row" v-if="manifest?.description">
            <span class="detail-label">描述</span>
            <span class="detail-value">{{ manifest.description }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">ID</span>
            <span class="detail-value detail-mono">{{ store.detailExt.id }}</span>
          </div>
          <div class="detail-row" v-if="store.detailExt.installed_at">
            <span class="detail-label">安装时间</span>
            <span class="detail-value">{{ formatDate(store.detailExt.installed_at) }}</span>
          </div>
          <div class="detail-row" v-if="store.detailExt.install_method">
            <span class="detail-label">安装方式</span>
            <span class="detail-value">{{ store.detailExt.install_method === 'git' ? 'Git' : 'ZIP' }}</span>
          </div>
        </section>

        <!-- 权限 -->
        <section class="detail-section" v-if="manifest?.permissions?.length">
          <h4 class="detail-section-title">权限</h4>
          <ul class="detail-list">
            <li v-for="p in manifest.permissions" :key="p" class="detail-list-item">{{ p }}</li>
          </ul>
        </section>

        <!-- 扩展点 -->
        <section class="detail-section" v-if="hasExtPoints">
          <h4 class="detail-section-title">扩展点</h4>
          <div v-if="manifest.ext_points?.backend?.length" class="detail-row">
            <span class="detail-label">后端钩子</span>
            <span class="detail-value">
              <code v-for="bp in manifest.ext_points.backend" :key="bp" class="detail-code">{{ bp }}</code>
            </span>
          </div>
          <div v-if="manifest.ext_points?.frontend?.length" class="detail-row">
            <span class="detail-label">前端面板</span>
            <span class="detail-value">
              <code v-for="fp in manifest.ext_points.frontend" :key="fp" class="detail-code">{{ fp }}</code>
            </span>
          </div>
        </section>

        <!-- 功能开关 -->
        <section class="detail-section" v-if="features.length">
          <h4 class="detail-section-title">功能开关</h4>
          <div
            v-for="feat in features"
            :key="feat.id"
            class="feature-item"
          >
            <div class="feature-info">
              <span class="feature-label">{{ feat.label }}</span>
              <span class="feature-desc" v-if="feat.description">{{ feat.description }}</span>
            </div>
            <label class="feature-toggle">
              <input
                type="checkbox"
                :checked="!!settings.features[feat.id]"
                @change="onFeatureChange(feat.id, $event.target.checked)"
              />
              <span class="toggle-slider" />
            </label>
          </div>
        </section>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import { useResizableDrawer } from '@/composables/useResizableDrawer';
import { extensionsApi } from '@/api/extensions';
import { useAlertStore } from '@/stores/alert';

const store = useExtensionsStore();
const alert = useAlertStore();
const { drawerWidth, resizing, onResizeStart } = useResizableDrawer('detail', { defaultWidth: 360 });
const detailLoading = ref(false);
const manifest = ref(null);

watch(() => store.detailExt, async (ext) => {
  if (!ext) {
    manifest.value = null;
    detailLoading.value = false;
    return;
  }
  detailLoading.value = true;
  try {
    manifest.value = await extensionsApi.getManifest(ext.id);
  } catch {
    manifest.value = null;
  } finally {
    detailLoading.value = false;
  }
}, { immediate: true });

const features = computed(() => manifest.value?.features || []);
const settings = computed(() => store.detailSettings || { features: {} });
const hasExtPoints = computed(() => {
  return (manifest.value?.ext_points?.backend?.length ||
          manifest.value?.ext_points?.frontend?.length);
});

async function onFeatureChange(featureId, value) {
  try {
    await store.toggleFeature(store.detailExt.id, featureId, value);
  } catch (e) {
    alert.show('保存设置失败：' + (e?.message || '未知错误'));
  }
}

function formatDate(isoStr) {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    return d.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  } catch {
    return isoStr;
  }
}
</script>

<style scoped>
.drawer-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 0;
  background: #fff;
  border-left: 1px solid #e5e5e5;
  overflow: hidden;
  transition: width 0.2s ease;
  z-index: 100;
}

.drawer-panel.open {
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.08);
}

.drawer-resize-handle {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  cursor: col-resize;
  z-index: 10;
}
.drawer-resize-handle:hover {
  background: rgba(74, 144, 217, 0.3);
}

.drawer-body {
  padding: 20px 24px 40px;
  height: 100%;
  overflow-y: auto;
}

/* 标题 */
.detail-header {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.detail-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.detail-close:hover {
  background: #f5f5f5;
  color: #333;
}

.detail-meta {
  display: flex;
  gap: 12px;
  margin-top: 6px;
  font-size: 13px;
  color: #888;
}

/* 分区 */
.detail-section {
  margin-bottom: 20px;
}

.detail-section-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.detail-row {
  display: flex;
  gap: 12px;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.6;
}

.detail-label {
  color: #888;
  flex-shrink: 0;
  min-width: 60px;
}

.detail-value {
  color: #555;
}

.detail-mono {
  font-family: monospace;
  font-size: 12px;
}

.detail-list {
  margin: 0;
  padding: 0 0 0 16px;
  list-style: disc;
}

.detail-list-item {
  font-size: 13px;
  color: #555;
  padding: 2px 0;
  font-family: monospace;
}

.detail-code {
  display: inline-block;
  background: #f5f5f5;
  padding: 1px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 12px;
  color: #555;
  margin: 1px 2px;
}

/* 功能开关 */
.feature-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}
.feature-item:last-child {
  border-bottom: none;
}

.feature-info {
  flex: 1;
  min-width: 0;
}

.feature-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.feature-desc {
  display: block;
  font-size: 12px;
  color: #999;
  margin-top: 2px;
}

.feature-toggle {
  position: relative;
  width: 40px;
  height: 22px;
  flex-shrink: 0;
  cursor: pointer;
}

.feature-toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: #ccc;
  border-radius: 11px;
  transition: background 0.2s;
}
.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 18px;
  height: 18px;
  background: #fff;
  border-radius: 50%;
  transition: transform 0.2s;
}

.feature-toggle input:checked + .toggle-slider {
  background: #4a90d9;
}
.feature-toggle input:checked + .toggle-slider::after {
  transform: translateX(18px);
}

.detail-loading {
  text-align: center;
  color: #999;
  padding: 32px 0;
  font-size: 14px;
}
</style>
