// frontend/src/extensions/useExtensionApi.js
import { useChatStore } from '@/stores/chat';
import { useSettingsStore } from '@/stores/settings';

/**
 * 扩展可用的核心 API。
 * 扩展组件通过 props.api 调用，而非直接 import。
 * 未来可在此处添加权限校验。
 */
export function createExtensionApi(extensionId) {
  return {
    getConversation(id) {
      const chatStore = useChatStore();
      return chatStore.conversations.find(c => c.id === id) || null;
    },
    getCurrentConversation() {
      const chatStore = useChatStore();
      if (!chatStore.activeConvId) return null;
      return { id: chatStore.activeConvId };
    },
    getMessages(convId) {
      const chatStore = useChatStore();
      if (convId) {
        const conv = chatStore.conversations.find(c => c.id === convId);
        return conv?.messages || [];
      }
      return chatStore.messages;
    },
    getSettings() {
      const settingsStore = useSettingsStore();
      return settingsStore.activePreset || settingsStore.presets[0] || null;
    },
    getWorldInfo() {
      // MVP 阶段 World Info 暂未实现，返回空
      return [];
    },
  };
}

export function useExtensionApi(extensionId) {
  return createExtensionApi(extensionId);
}
