// A single player and separately selected reading panel for Media Extended notes.
(() => {
  const initialized = new WeakSet();

  function setup(root) {
    if (initialized.has(root)) return;
    initialized.add(root);
    const rows = [...root.querySelectorAll(".blog-media-entry")];
    const panels = [...root.querySelectorAll(".blog-media-detail")];
    const previous = root.querySelector("[data-note-prev]");
    const next = root.querySelector("[data-note-next]");
    const play = root.querySelector("[data-note-play]");
    const status = root.querySelector("[data-note-status]");
    let selected = 0, video, listeners, requested;

    const divider = root.querySelector(".blog-media-divider");
    let drag;
    function resize(width) {
      width = Math.max(25, Math.min(70, width));
      root.style.setProperty("--media-left", `${width}fr`);
      root.style.setProperty("--media-right", `${100 - width}fr`);
      divider.setAttribute("aria-valuenow", String(Math.round(width)));
      window.dispatchEvent(new Event("resize"));
    }
    divider.addEventListener("pointerdown", event => {
      if (event.button !== 0 || !event.isPrimary) return;
      const gap = parseFloat(getComputedStyle(root).columnGap);
      const available = root.getBoundingClientRect().width - divider.getBoundingClientRect().width - 2 * gap;
      drag = { x: event.clientX, width: root.querySelector(".blog-media-left").getBoundingClientRect().width, available };
      divider.setPointerCapture(event.pointerId);
      root.classList.add("is-resizing");
      event.preventDefault();
      divider.focus();
    });
    divider.addEventListener("pointermove", event => {
      if (drag) resize(100 * (drag.width + event.clientX - drag.x) / drag.available);
    });
    for (const name of ["pointerup", "pointercancel"]) {
      divider.addEventListener(name, event => {
        if (divider.hasPointerCapture(event.pointerId)) divider.releasePointerCapture(event.pointerId);
      });
    }
    divider.addEventListener("lostpointercapture", () => {
      drag = undefined;
      root.classList.remove("is-resizing");
    });
    divider.addEventListener("keydown", event => {
      const width = Number(divider.getAttribute("aria-valuenow"));
      const sizes = { ArrowLeft: width - 2, ArrowRight: width + 2, Home: 25, End: 70 };
      if (event.key in sizes) { event.preventDefault(); resize(sizes[event.key]); }
    });

    function position() {
      let active = -1;
      if (video) rows.forEach((row, index) => {
        if (row.hasAttribute("data-note-time") && video.currentTime >= Number(row.dataset.noteTime)) active = index;
      });
      rows.forEach((row, index) => { row.querySelector(".blog-media-playing").hidden = index !== active; });
    }

    function select(index) {
      selected = index;
      panels.forEach((panel, i) => { panel.hidden = i !== selected; });
      rows.forEach((row, i) => {
        row.classList.toggle("is-reading", i === selected);
        row.querySelector("[data-note-select]").setAttribute("aria-current", String(i === selected));
      });
      root.querySelector("[data-note-count]").textContent = `笔记 ${selected + 1} / ${rows.length}`;
      play.disabled = !video || !rows[selected].hasAttribute("data-note-time");
      previous.disabled = selected === 0;
      next.disabled = selected === rows.length - 1;
      position();
      // Keep native lazy-loaded images and math layout informed when revealing a panel.
      window.dispatchEvent(new Event("resize"));
    }

    function jump(target, startPlaying = false) {
      if (!video) return;
      requested = { target, startPlaying };
      const apply = () => {
        if (!root.isConnected || !video) return;
        if (Number.isFinite(video.duration) && target > video.duration) {
          status.textContent = "该时间点超出实际视频时长，请核对笔记。";
          return;
        }
        video.currentTime = target;
        requested = undefined;
        status.textContent = "";
        if (startPlaying) video.play().catch(() => { status.textContent = "请使用播放器中的播放按钮开始播放。"; });
      };
      if (video.readyState) apply();
      else video.addEventListener("loadedmetadata", apply, { once: true, signal: listeners.signal });
    }

    function seek(index, startPlaying = false) {
      select(index);
      jump(Number(rows[index].dataset.noteTime), startPlaying);
    }

    function connect(element) {
      listeners?.abort();
      video = element;
      listeners = new AbortController();
      for (const name of ["timeupdate", "seeked", "loadedmetadata"]) {
        video.addEventListener(name, position, { signal: listeners.signal });
      }
      root.querySelectorAll("[data-note-seek]").forEach(button => { button.disabled = false; });
      root.querySelectorAll("[data-note-inline-time]").forEach(button => { button.disabled = false; });
      select(selected);
      if (requested) jump(requested.target, requested.startPlaying);
    }

    rows.forEach((row, index) => {
      row.querySelector("[data-note-select]").addEventListener("click", () => select(index));
      const time = row.querySelector("[data-note-seek]");
      if (time) { time.disabled = true; time.addEventListener("click", () => seek(index)); }
    });
    previous.addEventListener("click", () => { if (selected > 0) select(selected - 1); });
    next.addEventListener("click", () => { if (selected + 1 < rows.length) select(selected + 1); });
    play.addEventListener("click", () => seek(selected, true));
    root.querySelectorAll("[data-note-inline-time]").forEach(button => {
      button.disabled = true;
      button.addEventListener("click", () => jump(Number(button.dataset.noteInlineTime)));
    });
    root.addEventListener("blog-player-ready", event => connect(event.detail.video));
    // Each included article keeps its local anchors in its own detail panel.
    panels.forEach(panel => {
      const anchors = new Map();
      panel.querySelectorAll("[id]").forEach(element => {
        const original = element.id;
        element.id = `${panel.id}-${original}`;
        anchors.set(original, element.id);
      });
      panel.querySelectorAll('a[href^="#"]').forEach(link => {
        const original = decodeURIComponent(link.hash.slice(1));
        if (anchors.has(original)) link.hash = anchors.get(original);
      });
    });
    const native = root.querySelector("video");
    if (native) connect(native);
    else select(0);
  }

  function initialize() {
    document.body.classList.toggle("blog-media-page", !!document.querySelector("[data-media-notes]"));
    document.querySelectorAll("[data-media-notes]").forEach(setup);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
})();
