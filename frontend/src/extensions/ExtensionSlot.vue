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
import { ref, watch, onMounted } from 'vue';
import { useExtensionsStore } from '@/stores/extensions';
import { createExtensionApi } from './useExtensionApi';

const props = defineProps({
  name: { type: String, required: true },
  message: { type: Object, default: null },
  conversation: { type: Object, default: null },
});

const extensionsStore = useExtensionsStore();
const components = ref([]);
const loadedIds = new Set();

async function loadExtensionFrontend(ext) {
  if (!ext.frontend || loadedIds.has(ext.id)) return;
  loadedIds.add(ext.id);

  try {
    const resp = await fetch(`/api/extensions/${ext.id}/frontend`);
    if (!resp.ok) return;
    const code = await resp.text();
    // 动态执行扩展脚本（脚本自己注册到 window.__EXTENSION_REGISTRY__）
    const script = document.createElement('script');
    script.textContent = code;
    document.head.appendChild(script);
    // 等待一小段让脚本执行
    await new Promise(r => setTimeout(r, 50));
  } catch (e) {
    console.warn(`[ExtensionSlot] 加载扩展 ${ext.id} 前端失败:`, e);
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
          comp: Comp,
          props: {
            message: props.message,
            conversation: props.conversation,
            api: createExtensionApi(ext.id),
          },
        });
      }
    }
  }
  components.value = result;
}

onMounted(async () => {
  // 先加载所有前端扩展
  for (const ext of extensionsStore.enabledExtensions) {
    await loadExtensionFrontend(ext);
  }
  loadComponents();
});

watch(() => extensionsStore.enabledExtensions, async () => {
  for (const ext of extensionsStore.enabledExtensions) {
    await loadExtensionFrontend(ext);
  }
  loadComponents();
}, { deep: true });
</script>

<style scoped>
.extension-slot {
  /* 插槽容器无默认样式，扩展自行控制 */
}
</style>
