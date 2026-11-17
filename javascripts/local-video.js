// Enhance local resource cards while retaining native browser video decoding.
(() => {
  const assets = new URL("artplayer/artplayer.js", document.currentScript.src);
  const players = new Map();
  const pending = new WeakSet();
  let library;

  function holdSpeed(player, container) {
    let timer, pressed = false, originalRate;
    const hint = player.layers.add({
      name: "hold-speed", html: "3× 加速中",
      style: { display: "none", position: "absolute", width: "max-content", height: "auto", whiteSpace: "nowrap",
        top: "12%", left: "50%", transform: "translateX(-50%)",
        padding: "6px 12px", borderRadius: "4px", background: "rgba(0,0,0,.65)",
        color: "#fff", pointerEvents: "none" },
    });
    const editable = (target) => target.isContentEditable ||
      target.closest?.("input, textarea, select, [role='textbox'], [role='slider']");

    function finish(seek = false) {
      if (!pressed) return;
      clearTimeout(timer);
      pressed = false;
      hint.style.display = "none";
      if (originalRate !== undefined) {
        player.playbackRate = originalRate;
        originalRate = undefined;
      } else if (seek) {
        player.forward = player.constructor.SEEK_STEP;
      }
    }
    const cancel = () => finish();

    // Capture only our shortcut before ArtPlayer's immediate ArrowRight seek.
    player.events.proxy(document, "keydown", (event) => {
      if (event.code !== "ArrowRight" || !player.isFocus || document.hidden ||
          event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || editable(event.target) ||
          (event.target !== document.body && !container.contains(event.target))) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      if (pressed || event.repeat) return;
      pressed = true;
      timer = setTimeout(() => {
        if (!container.isConnected || document.hidden || !player.isFocus) { cancel(); return; }
        originalRate = player.playbackRate;
        player.playbackRate = 3;
        hint.style.display = "block";
      }, 400);
    }, true);
    player.events.proxy(document, "keyup", (event) => {
      if (event.code === "ArrowRight" && pressed) finish(true);
    }, true);
    player.events.proxy(window, "blur", cancel);
    player.events.proxy(document, "visibilitychange", () => { if (document.hidden) cancel(); });
    player.events.proxy(document, "focusin", (event) => {
      if (!container.contains(event.target) || editable(event.target)) cancel();
    });
    for (const event of ["blur", "destroy", "video:pause", "video:ended"]) player.on(event, cancel);
  }

  function subtitles(player, video, container) {
    const identifier = video.dataset.resourceId;
    if (!identifier) return;
    const api = new URL(`/local-subtitles/${identifier}/`, video.src);
    let token, timer, selected, trackRevision, closed = false, requesting = false;
    let state = { status: "idle", tracks: [] };
    const text = (value) => {
      const element = document.createElement("span");
      element.textContent = value;
      return element;
    };
    const alive = () => !closed && container.isConnected;
    const running = () => ["queued", "running"].includes(state.status);

    async function request(action, generate = false) {
      const response = await fetch(new URL(action, api), generate ? {
        method: "POST", headers: { "X-Blog-Subtitle-Token": token },
      } : {});
      const result = await response.json();
      if (!response.ok) throw new Error(result.message || "字幕服务暂不可用");
      return result;
    }

    async function choose(item) {
      selected = item.value;
      if (item.value === "off") {
        player.subtitle.show = false;
      } else {
        await player.subtitle.switch(item.value, { type: "vtt" });
        if (alive() && selected === item.value) player.subtitle.show = true;
      }
      return text(item.label).innerHTML;
    }

    function render() {
      const choices = state.tracks.map((track) => ({
        html: text(track.label), label: track.label,
        value: new URL(`track?index=${track.index}&revision=${track.revision}`, api).href,
      }));
      const off = { html: "关闭字幕", label: "关闭", value: "off" };
      const revision = JSON.stringify(state.tracks);
      if (trackRevision !== revision) {
        trackRevision = revision;
        const automatic = selected !== "off" && choices.length && !choices.some((item) => item.value === selected);
        if (automatic) selected = choices[0].value;
        const current = [off, ...choices].find((item) => item.value === selected);
        player.setting.update({
          name: "local-subtitles", html: "字幕", tooltip: current ? text(current.label).innerHTML : "暂无",
          selector: [off, ...choices].map((item) => ({ ...item, default: item.value === selected })),
          async onSelect(item) {
            try { return await choose(item); }
            catch { player.notice.show = "字幕读取失败，请检查 SRT 是否为 UTF-8 格式"; return "加载失败"; }
          },
        });
        if (automatic) choose(choices[0]).catch(() => { player.notice.show = "字幕读取失败，请检查 SRT 格式"; });
      }
      const button = player.setting.find("generate-subtitles");
      button.tooltip = running() ? "处理中" : state.status === "ready" ? "已就绪" :
        ["failed", "interrupted"].includes(state.status) ? "继续查询" : state.status === "uncertain" ? "需核对任务" : "可能计费";
      // Explain the upload at the action itself, without adding another page or dialog.
      button.$item.title = "音频将上传阿里云识别，可能产生费用；已有字幕不会被覆盖。" + (state.message || "");
    }

    async function refresh(generate = false) {
      if (!alive() || requesting) return;
      requesting = true;
      clearTimeout(timer);
      try {
        if (generate && !token) token = (await request("status")).token;
        state = await request(generate ? "generate" : "status", generate);
        token = state.token || token;
        if (!alive()) return;
        render();
        if (generate) player.notice.show = state.message || "已启动字幕任务";
      } catch (error) {
        if (alive()) player.notice.show = error.message;
      } finally {
        requesting = false;
        if (alive() && running()) timer = setTimeout(() => refresh(), 3000);
      }
    }

    player.setting.add({ name: "generate-subtitles", html: "生成字幕（云端）", tooltip: "可能计费",
      async onClick(item) {
        if (!running()) await refresh(true);
        else player.notice.show = state.message;
        return item.tooltip;
      },
    });
    player.on("setting", (show) => { if (show) refresh(); });
    player.on("destroy", () => { closed = true; clearTimeout(timer); });
    refresh();
  }

  async function enhance(video) {
    if (pending.has(video)) return;
    pending.add(video);
    let container;
    try {
      const { default: Artplayer } = await (library ||= import(assets.href));
      if (!video.isConnected) return;
      // Instant navigation replaces the head, including ArtPlayer's injected CSS.
      if (!document.getElementById("artplayer-style")) {
        const style = document.createElement("style");
        style.id = "artplayer-style";
        style.textContent = Artplayer.STYLE;
        document.head.append(style);
      }
      container = document.createElement("div");
      container.className = "blog-video-player";
      video.replaceWith(container);
      const player = new Artplayer({
        container,
        url: video.src,
        lang: "zh-cn",
        theme: "#009688",
        setting: true,
        fullscreen: true,
        pip: true,
        playsInline: true,
        subtitle: { escape: true },
        moreVideoAttr: { preload: "metadata" },
        settings: [{
          html: "播放速度",
          tooltip: "1.0×",
          range: [1, 0.5, 3, 0.1],
          onChange(item) {
            this.playbackRate = Math.round(item.range[0] * 10) / 10;
            return `${this.playbackRate.toFixed(1)}×`;
          },
          mounted(element, item) {
            // Set the value after ArtPlayer has applied min/max/step.
            item.$range.value = item.range[0];
            item.$range.setAttribute("aria-label", "播放速度");
          },
        }],
      });
      players.set(container, player);
      player.video.preservesPitch = true;
      holdSpeed(player, container);
      subtitles(player, video, container);
      player.on("video:loadedmetadata", () => {
        if (player.video.videoWidth && player.video.videoHeight) {
          container.style.aspectRatio = `${player.video.videoWidth} / ${player.video.videoHeight}`;
        }
      });
      // Stop any request or playback started by the native fallback.
      video.pause();
      video.removeAttribute("src");
      video.load();
      container.dispatchEvent(new CustomEvent("blog-player-ready", {
        bubbles: true, detail: { video: player.video },
      }));
    } catch (error) {
      if (container?.isConnected) container.replaceWith(video);
      console.error("视频播放器加载失败，保留原生播放控件", error);
    }
  }

  function initialize() {
    for (const [container, player] of players) {
      if (container.isConnected) continue;
      player.pause();
      player.destroy();
      players.delete(container);
    }
    document.querySelectorAll("video.blog-video").forEach(enhance);
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
  if (typeof document$ !== "undefined") document$.subscribe(initialize);
})();
