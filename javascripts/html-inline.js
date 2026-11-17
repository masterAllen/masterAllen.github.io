// Keep archived HTML styles and scripts isolated while sharing the page scroll.
(() => {
  const resourceOrigin = document.currentScript.dataset.resourceOrigin;
  const frames = new Set();
  const initialized = new WeakSet();

  // This function runs inside the sandbox and only reports its content height.
  function reportHeight() {
    let scheduled = false;
    let previous = 0;
    function schedule() {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(() => {
        scheduled = false;
        const body = document.body;
        const bounds = body.getBoundingClientRect();
        const margin = parseFloat(getComputedStyle(body).marginBottom) || 0;
        // Do not measure documentElement.scrollHeight: it includes the current
        // iframe viewport, preventing the frame from shrinking after reflow.
        const height = Math.ceil(Math.max(
          bounds.bottom + scrollY + margin,
          bounds.top + scrollY + body.scrollHeight,
          1,
        )) + 1;
        if (height === previous) return;
        previous = height;
        parent.postMessage({ type: "blog-html-height", height }, "*");
      });
    }
    new ResizeObserver(schedule).observe(document.body);
    new MutationObserver(schedule).observe(document.body, {
      subtree: true, childList: true, attributes: true, characterData: true,
    });
    document.addEventListener("load", schedule, true);
    window.addEventListener("resize", schedule);
    document.fonts.ready.then(schedule);
    schedule();
  }

  window.addEventListener("message", (event) => {
    const data = event.data;
    if (data?.type !== "blog-html-height" ||
        !Number.isFinite(data.height) || data.height <= 0) return;
    for (const frame of frames) {
      if (event.source !== frame.contentWindow) continue;
      frame.classList.add("embedded-html--expanded");
      const style = getComputedStyle(frame);
      const border = style.boxSizing === "border-box"
        ? parseFloat(style.borderTopWidth) + parseFloat(style.borderBottomWidth) : 0;
      frame.style.height = `${Math.ceil(data.height + border)}px`;
      break;
    }
  });

  async function expandHtml(frame) {
    const url = new URL(frame.src);
    if ((url.origin !== location.origin && url.origin !== resourceOrigin) || initialized.has(frame)) return;
    initialized.add(frame);
    try {
      const response = await fetch(url.href);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      // The HTML conversion pipeline reads UTF-8. Reject invalid bytes rather
      // than silently corrupting a legacy document; its original iframe stays.
      const source = new TextDecoder("utf-8", { fatal: true }).decode(await response.arrayBuffer());
      const document = new DOMParser().parseFromString(source, "text/html");
      if (!document.querySelector("base[href]")) {
        const base = document.createElement("base");
        base.href = url.href;
        document.head.prepend(base);
      }
      const style = document.createElement("style");
      style.textContent = "html,body{height:auto!important;min-height:0!important;max-height:none!important}html{overflow-y:hidden!important}";
      document.head.append(style);
      const bridge = document.createElement("script");
      bridge.textContent = `(${reportHeight.toString()})();`;
      document.body.append(bridge);
      if (!frame.isConnected) return;
      frames.add(frame);
      // Retain the original sandbox (without allow-same-origin). srcdoc keeps
      // the original page's styles separate from the surrounding blog.
      frame.srcdoc = `<!doctype html>\n${document.documentElement.outerHTML}`;
    } catch (error) {
      console.error("Inline HTML expansion failed; keeping original embed", error);
    }
  }

  function initialize() {
    for (const frame of frames) {
      if (!frame.isConnected) frames.delete(frame);
    }
    document.querySelectorAll("iframe.embedded-html").forEach(expandHtml);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
})();
