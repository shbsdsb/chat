// frontend/src/composables/useMessageAssembler.js

/**
 * 组装提示词条目和对话历史为完整 messages 数组。
 *
 * 规则：
 * 1. entries 按 order 排序
 * 2. 过滤 enabled=false 和 role=null 的条目
 * 3. 遍历 → 相邻同 role 合并（content 用 \n\n 分隔）
 * 4. 遇到 __chat_history__ → 展开为 conversationMessages
 * 5. __chat_history__ 是硬边界，不跨边界合并
 *
 * @param {Array} entries - 提示词条目（含 __chat_history__）
 * @param {Array} conversationMessages - 对话历史 [{role, content}]
 * @returns {Array} 组装后的 messages [{role, content}]
 */
export function assembleMessages(entries, conversationMessages) {
  if (!entries || entries.length === 0) {
    return conversationMessages ? [...conversationMessages] : [];
  }

  // 按 order 排序
  const sorted = [...entries].sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

  const result = [];

  let pendingRole = null;
  let pendingContents = [];

  /**
   * 刷新缓冲：将当前积累的同 role 内容合并为一条 message 写入 result
   */
  function flushPending() {
    if (pendingContents.length > 0) {
      result.push({
        role: pendingRole,
        content: pendingContents.join("\n\n"),
      });
      pendingRole = null;
      pendingContents = [];
    }
  }

  let chatHistoryInserted = false;

  for (const entry of sorted) {
    // --- chat_history 占位符 ---
    if (entry.id === "__chat_history__") {
      if (chatHistoryInserted) continue; // 防御：重复出现跳过
      chatHistoryInserted = true;

      flushPending(); // 先刷新边界前的缓冲区

      // 展开对话历史（保持原有 role，不合并）
      if (conversationMessages && conversationMessages.length > 0) {
        for (const msg of conversationMessages) {
          result.push({ role: msg.role, content: msg.content });
        }
      }
      continue;
    }

    // --- 跳过条件 ---
    if (entry.enabled === false) continue;
    if (entry.role === null || entry.role === undefined) continue;

    // --- 同 role 合并 ---
    if (entry.role === pendingRole) {
      pendingContents.push(entry.content || "");
    } else {
      flushPending();
      pendingRole = entry.role;
      pendingContents = [entry.content || ""];
    }
  }

  // 处理 chat_history 之后的缓冲区
  flushPending();

  return result;
}

/**
 * Vue composable 入口（便于在组件中使用）。
 */
export function useMessageAssembler() {
  return { assembleMessages };
}
