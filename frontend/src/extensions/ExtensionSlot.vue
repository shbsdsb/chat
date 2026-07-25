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
  if (!ext.frontend || loadedIds.has(ext.id)) {
    console.log(`[ExtensionSlot:${props.name}] skip ${ext.id}: frontend=${ext.frontend} loaded=${loadedIds.has(ext.id)}`);
    return;
  }
  loadedIds.add(ext.id);
  console.log(`[ExtensionSlot:${props.name}] loading frontend for ${ext.id}`);

  try {
    const resp = await fetch(`/api/extensions/${ext.id}/frontend`);
    console.log(`[ExtensionSlot:${props.name}] fetch ${ext.id}: status=${resp.status}`);
    if (!resp.ok) return;
    const code = await resp.text();
    console.log(`[ExtensionSlot:${props.name}] got ${code.length} chars for ${ext.id}`);
    const script = document.createElement('script');
    script.textContent = code;
    document.head.appendChild(script);
    console.log(`[ExtensionSlot:${props.name}] script injected for ${ext.id}`);
  } catch (e) {
    console.warn(`[ExtensionSlot:${props.name}] 加载 ${ext.id} 失败:`, e);
  }
}

function loadComponents() {
  const registry = window.__EXTENSION_REGISTRY__ || {};
  console.log(`[ExtensionSlot:${props.name}] loadComponents: registry keys=`, Object.keys(registry), 'enabledExts=', extensionsStore.enabledExtensions.map(e => e.id));
  const result = [];
  for (const ext of extensionsStore.enabledExtensions) {
    const extRegistry = registry[ext.id];
    console.log(`[ExtensionSlot:${props.name}]   ext ${ext.id}: in registry=${!!extRegistry}`);
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
  console.log(`[ExtensionSlot:${props.name}] loadComponents: result=${result.length} components`);
  components.value = result;
}

onMounted(() => {
  console.log(`[ExtensionSlot:${props.name}] mounted, items=`, extensionsStore.items.length, 'enabled=', extensionsStore.enabledExtensions.length);
  for (const ext of extensionsStore.enabledExtensions) {
    loadExtensionFrontend(ext);
  }
  loadComponents();
});

watch(() => extensionsStore.items, () => {
  console.log(`[ExtensionSlot:${props.name}] items changed, count=`, extensionsStore.items.length);
  for (const ext of extensionsStore.enabledExtensions) {
    loadExtensionFrontend(ext);
  }
  loadComponents();
}, { deep: true });
</script>

<style scoped>
.extension-slot {
  /* 插槽容器无默认样式，扩展自行控制 */
}
</style>
