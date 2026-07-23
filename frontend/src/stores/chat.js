import { defineStore } from "pinia";
import * as conversationsApi from "@/api/conversations";
import { sse } from "@/api/sse";

const NEW_CONV = "__new__";

// ── 工具函数 ────────────────────────────────────
function sortByLastMessage(convs) {
  convs.sort((a, b) => (b.lastMessageAt || "").localeCompare(a.lastMessageAt || ""));
}

function applyChunk(msg, chunk) {
  if (chunk.reasoning_delta) {
    msg.reasoning_content = (msg.reasoning_content || "") + chunk.reasoning_delta;
  }
  if (chunk.delta) {
    msg.content = (msg.content || "") + chunk.delta;
  }
}

export const useChatStore = defineStore("chat", {
  state: () => ({
    conversations: [],
    activeConvId: null,
    messages: [],
    isStreaming: false,
    abortController: null,
    aiVersionIndex: 0,
    aiVersions: {},
    editingMessageId: null,
  }),

  actions: {
    async loadConversations() {
      this.conversations = await conversationsApi.list();
      this.conversations.forEach((c) => {
        c.lastMessageAt = c.updated_at;
      });
      sortByLastMessage(this.conversations);
    },

    // 进入空白对话页，不创建后端记录
    createConversation() {
      this.activeConvId = NEW_CONV;
      this.messages = [];
      this.aiVersions = {};
    },

    async deleteConversation(id) {
      await conversationsApi.remove(id);
      this.conversations = this.conversations.filter((c) => c.id !== id);
      if (this.activeConvId === id) {
        this.activeConvId = null;
        this.messages = [];
      }
    },

    async renameConversation(id, title) {
      const updated = await conversationsApi.rename(id, title);
      const idx = this.conversations.findIndex((c) => c.id === id);
      if (idx !== -1) this.conversations[idx] = updated;
    },

    async selectConversation(id) {
      this.activeConvId = id;
      this.aiVersionIndex = 0;
      if (id === NEW_CONV) {
        this.messages = [];
        return;
      }
      const data = await conversationsApi.detail(id);
      this.messages = data.messages || [];
    },

    async sendMessage(content) {
      if (this.isStreaming) return;

      // 无活跃会话 → 视为新对话
      if (!this.activeConvId) {
        this.activeConvId = NEW_CONV;
      }

      // 首次发送 → 先创建后端对话记录
      if (this.activeConvId === NEW_CONV) {
        const title = content.slice(0, 20);
        const conv = await conversationsApi.create(title);
        conv.lastMessageAt = new Date().toISOString();
        this.activeConvId = conv.id;
        this.conversations.unshift(conv);
        sortByLastMessage(this.conversations);
      } else {
        const now = new Date().toISOString();
        const idx = this.conversations.findIndex((c) => c.id === this.activeConvId);
        if (idx !== -1) {
          this.conversations[idx].lastMessageAt = now;
        }
        sortByLastMessage(this.conversations);
      }

      const userMsg = {
        id: "temp-" + Date.now(),
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      this.messages.push(userMsg);

      const assistantMsg = {
        id: "temp-" + (Date.now() + 1),
        role: "assistant",
        content: "",
        reasoning_content: "",
        created_at: new Date().toISOString(),
      };
      this.messages.push(assistantMsg);
      this.isStreaming = true;

      const es = sse(`/conversations/${this.activeConvId}/chat`, {
        method: "POST",
        body: JSON.stringify({ content }),
        onMessage: (chunk) => {
          if (chunk.stopped) {
            this.isStreaming = false;
            return;
          }
          const last = this.messages[this.messages.length - 1];
          if (last && last.role === "assistant") {
            applyChunk(last, chunk);
          }
          if (chunk.done) {
            this.isStreaming = false;
          }
        },
        onError: (err) => {
          this.isStreaming = false;
          console.error("SSE error:", err);
        },
        onDone: () => {
          this.isStreaming = false;
        },
      });

      this.abortController = es;
    },

    stopStreaming() {
      if (this.abortController) {
        conversationsApi.stopGeneration(this.activeConvId);
        this.abortController.close();
        this.abortController = null;
      }
      this.isStreaming = false;
    },

    async editMessage(id, content) {
      const updated = await conversationsApi.editMessage(this.activeConvId, id, content);
      const idx = this.messages.findIndex((m) => m.id === id);
      if (idx !== -1) {
        this.messages[idx] = updated;
        this.messages = this.messages.slice(0, idx + 1);
      }
      this.editingMessageId = null;
    },

    enterEditMode(id) {
      this.editingMessageId = id;
    },

    exitEditMode() {
      this.editingMessageId = null;
    },

    replayMessage(id) {
      const assistantMsg = this.messages.find((m) => m.id === id && m.role === "assistant");
      if (!assistantMsg || this.isStreaming) return;

      if (!this.aiVersions[id]) {
        this.aiVersions[id] = [assistantMsg.content];
        this.aiVersionIndex = 0;
      }

      this.isStreaming = true;
      const newContent = { value: "" };
      const newReasoning = { value: "" };

      const es = sse(`/conversations/${this.activeConvId}/regenerate`, {
        method: "POST",
        body: JSON.stringify({}),
        onMessage: (chunk) => {
          if (chunk.stopped) {
            this.isStreaming = false;
            return;
          }
          if (chunk.reasoning_delta) {
            newReasoning.value += chunk.reasoning_delta;
            assistantMsg.reasoning_content = newReasoning.value;
          }
          if (chunk.delta) {
            newContent.value += chunk.delta;
            assistantMsg.content = newContent.value;
          }
          if (chunk.done) {
            assistantMsg.reasoning_content = newReasoning.value;
            this.aiVersions[id].push(newContent.value);
            this.aiVersionIndex = this.aiVersions[id].length - 1;
            this.isStreaming = false;
          }
        },
        onError: (err) => {
          this.isStreaming = false;
          console.error("Replay error:", err);
        },
        onDone: () => {
          this.isStreaming = false;
        },
      });

      this.abortController = es;
    },

    switchVersion(id, dir) {
      const versions = this.aiVersions[id];
      if (!versions || versions.length <= 1) return;

      const newIdx = this.aiVersionIndex + dir;
      if (newIdx < 0 || newIdx >= versions.length) return;

      this.aiVersionIndex = newIdx;
      const msg = this.messages.find((m) => m.id === id);
      if (msg) {
        msg.content = versions[newIdx];
      }
    },
  },
});
