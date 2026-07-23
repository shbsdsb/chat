import { ref } from "vue";

export function useResizableDrawer(options = {}) {
  const {
    direction = "left",
    minWidth = 220,
    maxWidth = 700,
    defaultWidth = 320,
  } = options;

  const width = ref(defaultWidth);
  const isResizing = ref(false);

  function startResize(e) {
    e.preventDefault();
    isResizing.value = true;
    document.body.style.userSelect = "none";
    document.body.style.cursor = "col-resize";

    const startX = e.clientX;
    const startW = width.value;

    function onMove(ev) {
      const delta = direction === "left" ? ev.clientX - startX : startX - ev.clientX;
      width.value = Math.max(minWidth, Math.min(maxWidth, startW + delta));
    }

    function onUp() {
      isResizing.value = false;
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    }

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }

  return { width, isResizing, startResize };
}
