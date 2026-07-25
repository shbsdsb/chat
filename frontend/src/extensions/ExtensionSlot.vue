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

onMounted(() => {
  loadComponents();
});

watch(() => extensionsStore.enabledExtensions, () => {
  loadComponents();
}, { deep: true });
</script>

<style scoped>
.extension-slot {
  /* 插槽容器无默认样式，扩展自行控制 */
}
</style>
