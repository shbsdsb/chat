<template>
  <div v-if="components.length" class="extension-slot" :data-slot="name">
    <component
      v-for="(item, idx) in components"
      :is="item.comp"
      :key="idx"
      v-bind="item.props || {}"
    />
  </div>
</template>

<script setup>
import { shallowRef, ref, watch, onMounted, markRaw } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import { createExtensionApi } from './useExtensionApi';
import { extensionsApi } from '@/api/extensions';

const props = defineProps({
  name: { type: String, required: true },
  message: { type: Object, default: null },
  conversation: { type: Object, default: null },
});

const extensionsStore = useExtensionsStore();
const components = shallowRef([]);
const loadedIds = (window.__EXTENSION_SCRIPTS_LOADED__ =
  window.__EXTENSION_SCRIPTS_LOADED__ || new Set());
const settingsMap = ref({});

async function loadSettings() {
  const map = {};
  await Promise.all(
    extensionsStore.enabledExtensions.map(async (ext) => {
      try {
        const s = await extensionsApi.getSettings(ext.id);
        map[ext.id] = s;
      } catch {
        map[ext.id] = { features: {} };
      }
    })
  );
  settingsMap.value = map;
}

async function loadExtensionFrontend(ext) {
  if (!ext.frontend || loadedIds.has(ext.id)) {
    return;
  }

  try {
    const resp = await fetch(`/api/extensions/${ext.id}/frontend`);
    if (!resp.ok) return;
    const code = await resp.text();
    const script = document.createElement('script');
    script.textContent = code;
    document.head.appendChild(script);
    loadedIds.add(ext.id);
  } catch (e) {
    console.error(`[ExtensionSlot] 扩展 ${ext.id} 加载失败:`, e);
  }
}

function loadComponents() {
  const registry = window.__EXTENSION_REGISTRY__ || {};
  const result = [];
  for (const ext of extensionsStore.enabledExtensions) {
    const extRegistry = registry[ext.id];
    if (!extRegistry) continue;
    for (const [slotName, comps] of Object.entries(extRegistry)) {
      if (slotName !== props.name) continue;
      for (const Comp of comps) {
        result.push({
          comp: markRaw(Comp),
          props: {
            message: props.message,
            conversation: props.conversation,
            api: createExtensionApi(ext.id),
            settings: settingsMap.value[ext.id] || { features: {} },
          },
        });
      }
    }
  }
  components.value = result;
}

async function loadAllAndRender() {
  await Promise.all(
    extensionsStore.enabledExtensions.map(e => loadExtensionFrontend(e))
  );
  await loadSettings();
  loadComponents();
}

onMounted(() => {
  loadAllAndRender();
});

watch(() => extensionsStore.items, () => {
  loadAllAndRender();
}, { deep: true });

// 监听功能开关变更（toggleFeature 完成后触发）→ 重新加载 settings 并更新组件 props
watch(() => extensionsStore.settingsVersion, async () => {
  if (!extensionsStore.settingsVersion) return; // 跳过初始值 0
  await loadSettings();
  loadComponents();
});
</script>

<style scoped>
.extension-slot {
  /* 插槽容器无默认样式，扩展自行控制 */
}
</style>
