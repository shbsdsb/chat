import { ref, watch } from 'vue';
import { safeRender, renderLive, isInCodeBlock } from './markdown/engine';
import { splitParagraphs, getCodeBlockRanges } from './markdown/splitter';
import { detectHtmlType, splitMixed, findEmbeddedHtmlDoc } from './markdown/htmlDetector';

export function useMarkdown(contentRef) {
  const frozenHtmls = ref([]);
  const liveHtml = ref('');
  const blocks = ref([]);
  const isCompleteHtml = ref(false);

  watch(
    () => contentRef.value,
    (content) => {
      if (!content) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        blocks.value = [];
        isCompleteHtml.value = false;
        return;
      }

      const htmlType = (() => {
        try {
          return detectHtmlType(content);
        } catch {
          return 'none';
        }
      })();

      // ── 完整 HTML 文档 ──
      if (htmlType === 'full') {
        frozenHtmls.value = [];
        liveHtml.value = '';
        blocks.value = [{ type: 'html', code: content }];
        isCompleteHtml.value = true;
        return;
      }

      isCompleteHtml.value = false;

      // ── 嵌入式 HTML 文档 ──
      const embedded = findEmbeddedHtmlDoc(content, getCodeBlockRanges(content));
      if (embedded) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        blocks.value = [];
        isCompleteHtml.value = false;

        const rendered = [];

        if (embedded.before) {
          rendered.push({ type: 'text', html: safeRender(embedded.before) });
        }

        try {
          rendered.push({ type: 'html', code: embedded.htmlDoc });
        } catch {
          rendered.push({ type: 'text', html: safeRender(embedded.htmlDoc) });
        }

        try {
          const afterBlocks = splitMixed(embedded.after);
          for (const b of afterBlocks) {
            if (b.type === 'text') {
              if (b.content.trim()) rendered.push({ type: 'text', html: safeRender(b.content) });
            } else {
              rendered.push(b);
            }
          }
        } catch {
          if (embedded.after.trim()) {
            rendered.push({ type: 'text', html: safeRender(embedded.after) });
          }
        }

        blocks.value = rendered;
        return;
      }

      // ── 混合内容 ──
      if (htmlType === 'mixed') {
        try {
          const paragraphs = splitParagraphs(content);
          if (paragraphs.length === 0) {
            frozenHtmls.value = [];
            liveHtml.value = '';
            blocks.value = [];
            return;
          }

          const frozenContent = paragraphs.slice(0, -1).join('\n\n');
          const liveContent = paragraphs[paragraphs.length - 1] || '';

          const mixedBlocks = splitMixed(frozenContent);
          const renderedBlocks = mixedBlocks.map(b => {
            if (b.type === 'text') {
              return { type: 'text', html: safeRender(b.content) };
            }
            return b;
          });

          blocks.value = renderedBlocks;
          frozenHtmls.value = [];
          liveHtml.value = renderLive(liveContent, isInCodeBlock(liveContent));
          return;
        } catch {
          // Fall through to the none-mode (pure markdown) path below
        }
      }

      // ── 纯文本 ──
      blocks.value = [];

      const paragraphs = splitParagraphs(content);
      if (paragraphs.length === 0) {
        frozenHtmls.value = [];
        liveHtml.value = '';
        return;
      }

      const frozen = paragraphs.slice(0, -1);
      frozenHtmls.value = frozen.map(p => safeRender(p));

      const last = paragraphs[paragraphs.length - 1];
      liveHtml.value = renderLive(last, isInCodeBlock(last));
    },
    { immediate: true }
  );

  return { frozenHtmls, liveHtml, blocks, isCompleteHtml };
}
