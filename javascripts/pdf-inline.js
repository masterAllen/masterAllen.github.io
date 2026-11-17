// Display existing PDF embeds one page at a time, with local page controls.
(() => {
  const assets = new URL("pdfjs/", document.currentScript.src);
  let library;
  let stylesheet;
  const viewers = new Map();

  function loadLibrary() {
    if (!stylesheet?.isConnected) {
      stylesheet = document.createElement("link");
      stylesheet.rel = "stylesheet";
      stylesheet.href = new URL("text-layer.css", assets).href;
      document.head.append(stylesheet);
    }
    if (!library) {
      library = import(new URL("pdf.min.js", assets).href).then((pdfjs) => {
        pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdf.worker.min.js", assets).href;
        return pdfjs;
      });
    }
    return library;
  }

  async function expandPdf(frame) {
    const url = new URL(frame.src);
    url.hash = "";
    const container = document.createElement("div");
    container.className = "inline-pdf";
    container.tabIndex = 0;
    container.setAttribute("role", "region");
    container.setAttribute("aria-label", frame.title || "PDF");
    const status = document.createElement("p");
    status.className = "inline-pdf__status";
    status.setAttribute("role", "status");
    status.textContent = "正在加载 PDF…";
    frame.replaceWith(container);
    container.append(status);

    try {
      const pdfjs = await loadLibrary();
      if (!container.isConnected) return;
      const loading = pdfjs.getDocument({
        url: url.href,
        cMapUrl: new URL("cmaps/", assets).href,
        cMapPacked: true,
        standardFontDataUrl: new URL("standard_fonts/", assets).href,
        wasmUrl: new URL("wasm/", assets).href,
        isEvalSupported: false,
      });
      viewers.set(container, () => loading.destroy());
      const pdf = await loading.promise;
      if (!container.isConnected) return;
      const stage = document.createElement("div");
      stage.className = "inline-pdf__stage";
      const element = document.createElement("div");
      element.className = "inline-pdf__page";
      element.setAttribute("role", "group");
      stage.append(element);
      const controls = document.createElement("div");
      controls.className = "inline-pdf__controls";
      const previous = document.createElement("button");
      previous.type = "button";
      previous.textContent = "‹ 上一页";
      const next = document.createElement("button");
      next.type = "button";
      next.textContent = "下一页 ›";
      const counter = document.createElement("span");
      counter.className = "inline-pdf__counter";
      counter.setAttribute("aria-live", "polite");
      controls.append(previous, counter, next);
      const settings = document.createElement("div");
      settings.className = "inline-pdf__settings";
      const zoomControls = document.createElement("span");
      zoomControls.className = "inline-pdf__zoom";
      const zoomOut = document.createElement("button");
      zoomOut.type = "button";
      zoomOut.textContent = "−";
      zoomOut.setAttribute("aria-label", "缩小 PDF");
      const zoomValue = document.createElement("output");
      zoomValue.textContent = "100%";
      const zoomIn = document.createElement("button");
      zoomIn.type = "button";
      zoomIn.textContent = "+";
      zoomIn.setAttribute("aria-label", "放大 PDF");
      const fit = document.createElement("button");
      fit.type = "button";
      fit.textContent = "适应页面";
      zoomControls.append("缩放", zoomOut, zoomValue, zoomIn, fit);
      const heightControls = document.createElement("span");
      heightControls.className = "inline-pdf__height";
      const heightDown = document.createElement("button");
      heightDown.type = "button";
      heightDown.textContent = "−";
      heightDown.setAttribute("aria-label", "减小阅读框高度");
      const heightValue = document.createElement("output");
      const heightUp = document.createElement("button");
      heightUp.type = "button";
      heightUp.textContent = "+";
      heightUp.setAttribute("aria-label", "增大阅读框高度");
      heightControls.append("高度", heightDown, heightValue, heightUp);
      settings.append(zoomControls, heightControls);
      container.replaceChildren(stage, controls, settings, status);
      const state = { element, revision: 0 };
      let number = 1;
      let zoom = 1;

      function release(state) {
        state.revision++;
        state.renderTask?.cancel();
        state.textLayer?.cancel();
        state.renderTask = state.textLayer = null;
        // Cancel the old render before a page change or resize.
        const canvas = state.element.querySelector("canvas");
        if (canvas) canvas.width = canvas.height = 0;
        state.element.replaceChildren();
        state.element.removeAttribute("data-rendered");
      }

      async function showPage(target) {
        if (target !== number) stage.scrollTo(0, 0);
        number = Math.max(1, Math.min(target, pdf.numPages));
        previous.disabled = number === 1;
        next.disabled = number === pdf.numPages;
        counter.textContent = `${number} / ${pdf.numPages}`;
        element.setAttribute("aria-label", `第 ${number} 页，共 ${pdf.numPages} 页`);
        release(state);
        const revision = state.revision;
        status.hidden = false;
        status.textContent = "正在加载 PDF…";
        stage.setAttribute("aria-busy", "true");
        try {
          const page = await pdf.getPage(number);
          if (revision !== state.revision || !container.isConnected) return;
          if (!stage.clientWidth || !stage.clientHeight) return;
          const original = page.getViewport({ scale: 1 });
          const viewport = page.getViewport({
            scale: zoom * Math.min(stage.clientWidth / original.width, stage.clientHeight / original.height),
          });
          element.style.width = `${viewport.width}px`;
          element.style.height = `${viewport.height}px`;
          const ratio = Math.min(window.devicePixelRatio || 1, 2);
          const canvas = document.createElement("canvas");
          canvas.width = Math.ceil(viewport.width * ratio);
          canvas.height = Math.ceil(viewport.height * ratio);
          canvas.setAttribute("aria-hidden", "true");
          const text = document.createElement("div");
          text.className = "textLayer";
          // PDF.js uses these variables to position selectable text over the canvas.
          element.style.setProperty("--total-scale-factor", viewport.scale * viewport.userUnit);
          element.style.setProperty("--scale-round-x", "1px");
          element.style.setProperty("--scale-round-y", "1px");
          element.append(canvas, text);
          state.renderTask = page.render({
            canvasContext: canvas.getContext("2d"),
            viewport,
            transform: [ratio, 0, 0, ratio, 0, 0],
          });
          await state.renderTask.promise;
          if (revision !== state.revision) return;
          state.textLayer = new pdfjs.TextLayer({
            textContentSource: page.streamTextContent(),
            container: text,
            viewport,
          });
          await state.textLayer.render();
          if (revision === state.revision) {
            element.dataset.rendered = "true";
            status.hidden = true;
          }
        } catch (error) {
          if (revision !== state.revision) return;
          console.error("PDF page rendering failed", error);
          release(state);
          stage.removeAttribute("aria-busy");
          status.textContent = "本页加载失败，请重试翻页或刷新页面。";
        } finally {
          if (revision === state.revision) stage.removeAttribute("aria-busy");
        }
      }

      previous.addEventListener("click", () => showPage(number - 1));
      next.addEventListener("click", () => showPage(number + 1));
      function setZoom(value) {
        zoom = Math.max(0.5, Math.min(value, 3));
        zoomValue.textContent = `${Math.round(zoom * 100)}%`;
        zoomOut.disabled = zoom === 0.5;
        zoomIn.disabled = zoom === 3;
        stage.scrollTo(0, 0);
        showPage(number);
      }
      zoomOut.addEventListener("click", () => setZoom(zoom - 0.25));
      zoomIn.addEventListener("click", () => setZoom(zoom + 0.25));
      fit.addEventListener("click", () => setZoom(1));
      function updateHeight() {
        heightValue.textContent = `${stage.offsetHeight}px`;
        heightDown.disabled = stage.offsetHeight <= 240;
        heightUp.disabled = stage.offsetHeight >= 1200;
      }
      function setHeight(value) {
        stage.style.height = `${Math.max(240, Math.min(value, 1200))}px`;
        stage.style.maxHeight = "none";
        updateHeight();
      }
      heightDown.addEventListener("click", () => setHeight(stage.offsetHeight - 20));
      heightUp.addEventListener("click", () => setHeight(stage.offsetHeight + 20));
      container.addEventListener("keydown", (event) => {
        if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey
            || event.target.isContentEditable
            || event.target.closest("a, input, textarea, select")) return;
        if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
        event.preventDefault();
        event.stopPropagation();
        showPage(number + (event.key === "ArrowRight" ? 1 : -1));
      });

      let size = "";
      const resize = new ResizeObserver(() => {
        const current = `${stage.clientWidth}x${stage.clientHeight}`;
        if (current === size) return;
        size = current;
        updateHeight();
        showPage(number);
      });
      resize.observe(stage);
      viewers.set(container, () => {
        resize.disconnect();
        release(state);
        loading.destroy();
      });
    } catch (error) {
      if (!container.isConnected) return;
      console.error("PDF loading failed", error);
      status.textContent = "PDF 加载失败，请刷新页面后重试。";
    }
  }

  function initialize() {
    for (const [container, dispose] of viewers) {
      if (container.isConnected) continue;
      dispose();
      viewers.delete(container);
    }
    document.querySelectorAll("iframe.embedded-pdf").forEach(expandPdf);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
})();
