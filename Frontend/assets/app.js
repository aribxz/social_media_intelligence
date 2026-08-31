/* ============================================================
   SMI Dashboard — shared helpers
   ============================================================ */

const SMI = (() => {
  const API_BASE = (window.location.protocol === "file:") ? "http://127.0.0.1:5000" : window.location.origin;

  const prefersReducedMotion =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const palette = {
    bg: "#0a0a0f",
    surface: "#121019",
    border: "#2a2440",
    accent: "#8b5cf6",
    accent2: "#a855f7",
    text: "#e7e5f0",
    textDim: "#9a93b3",
    positive: "#34d399",
    neutral: "#a855f7",
    negative: "#f87171",
  };

  /* ---------------- Fetch ---------------- */

  async function getJSON(path) {
    const url = `${API_BASE}${path}`;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    let res;
    try {
      res = await fetch(url, { signal: controller.signal });
    } catch (err) {
      clearTimeout(timeout);
      throw new Error(err.name === "AbortError" ? "timeout" : "network: " + err.message);
    }
    clearTimeout(timeout);
    if (!res.ok) {
      throw new Error(`http_${res.status} @ ${path}`);
    }
    return res.json();
  }

  /* ---------------- State rendering ---------------- */

  function renderLoading(container, message = "Loading analytics…") {
    container.innerHTML = `
      <div class="state-msg">
        <div class="spinner"></div>
        <div>${message}</div>
      </div>`;
  }

  function renderError(container, opts = {}) {
    const title = opts.title || "Data not available";
    const hint =
      opts.hint ||
      "This endpoint returned nothing. Make sure the Flask backend is running and analytics.py has been run to generate outputs.";
    container.innerHTML = `
      <div class="state-msg error">
        <div>${title}</div>
        <div class="hint">${hint}</div>
      </div>`;
  }

  /* ---------------- Scroll reveal ---------------- */

  function initReveal(root = document) {
    const items = root.querySelectorAll(".reveal");
    if (!items.length) return;

    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    items.forEach((el, i) => {
      el.style.transitionDelay = `${Math.min(i, 10) * 60}ms`;
      observer.observe(el);
    });
  }

  /* ---------------- KPI count-up ---------------- */

  function animateCount(el, target, opts = {}) {
    const duration = prefersReducedMotion ? 0 : opts.duration || 800;
    const decimals = opts.decimals || 0;
    const suffix = opts.suffix || "";
    const prefix = opts.prefix || "";

    if (!duration) {
      el.textContent = `${prefix}${target.toFixed(decimals)}${suffix}`;
      return;
    }

    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - p, 3); // ease-out cubic
      const value = target * eased;
      el.textContent = `${prefix}${value.toFixed(decimals)}${suffix}`;
      if (p < 1) requestAnimationFrame(tick);
      else el.textContent = `${prefix}${target.toFixed(decimals)}${suffix}`;
    }
    requestAnimationFrame(tick);
  }

  function formatCompact(n) {
    if (n === null || n === undefined || isNaN(n)) return "—";
    return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);
  }

  /* ---------------- Header ---------------- */

  function renderHeader(container) {
    const navLinks = [
      { href: "index.html", label: "Home" },
      { href: "about.html", label: "About" },
    ];
    const current = (location.pathname.split("/").pop() || "index.html").split("?")[0];
    const nav = navLinks
      .map((l) => `<a class="nav-link${l.href === current ? " active" : ""}" href="${l.href}">${escapeHTML(l.label)}</a>`)
      .join("");

    container.innerHTML = `
      <div class="brand">
        <span class="dot"></span>
        <span>SMI</span>
      </div>
      <nav class="header-nav" aria-label="Primary">${nav}</nav>
    `;
  }

  /* ---------------- Limitations banner ---------------- */

  async function renderLimitationsBanner(container) {
    try {
      const data = await getJSON("/api/limitations");
      const notes = data.notes || [];
      container.innerHTML = `
        <div class="limitations-banner reveal">
          <strong>Limitations of this analysis</strong>
          <ul>
            ${notes.map((n) => `<li>${escapeHTML(n)}</li>`).join("")}
          </ul>
        </div>`;
      initReveal(container);
    } catch (err) {
      container.innerHTML = "";
    }
  }

  function escapeHTML(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ---------------- Page transition curtain ---------------- */

  function initPageTransition() {
    if (prefersReducedMotion) return;

    // Soft fade-out, then navigate, when clicking an internal link.
    document.addEventListener("click", (e) => {
      const a = e.target.closest("a[href]");
      if (!a) return;
      const href = a.getAttribute("href");
      if (!href || href.startsWith("http") || href.startsWith("#") ||
          href.startsWith("mailto:") || href.startsWith("javascript:")) {
        return;
      }
      e.preventDefault();
      document.body.classList.add("is-leaving");
      let navigated = false;
      const go = () => {
        if (navigated) return;
        navigated = true;
        window.location.href = a.href;
      };
      document.body.addEventListener("transitionend", go, { once: true });
      setTimeout(go, 380); // fallback
    });
  }

  /* ---------------- Ambient background node field ---------------- */

  function initBackground() {
    if (prefersReducedMotion) return;

    const canvas = document.createElement("canvas");
    canvas.id = "bg-canvas";
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");

    let w = 0, h = 0, dpr = 1;
    function resize() {
      dpr = window.devicePixelRatio || 1;
      w = window.innerWidth;
      h = window.innerHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener("resize", resize);

    const count = Math.max(34, Math.min(72, Math.floor((w * h) / 22000)));
    const parts = [];
    for (let i = 0; i < count; i++) {
      parts.push({
        x: Math.random() * w,
        y: Math.random() * h,
        r: Math.random() * 2.2 + 1.2,
        vx: (Math.random() - 0.5) * 0.32,
        vy: (Math.random() - 0.5) * 0.32,
        a: Math.random() * 0.18 + 0.12,
        tw: Math.random() * Math.PI * 2,
        ts: 0.01 + Math.random() * 0.02,
      });
    }

    const LINK = 150;
    function frame() {
      ctx.clearRect(0, 0, w, h);

      // faint connecting lines between nearby nodes (network mesh)
      for (let i = 0; i < parts.length; i++) {
        for (let j = i + 1; j < parts.length; j++) {
          const dx = parts[i].x - parts[j].x;
          const dy = parts[i].y - parts[j].y;
          const d = Math.hypot(dx, dy);
          if (d < LINK) {
            ctx.beginPath();
            ctx.moveTo(parts[i].x, parts[i].y);
            ctx.lineTo(parts[j].x, parts[j].y);
            ctx.strokeStyle = `rgba(139, 92, 246, ${(0.10 * (1 - d / LINK)).toFixed(3)})`;
            ctx.lineWidth = 1;
            ctx.stroke();
          }
        }
      }

      for (const p of parts) {
        p.x += p.vx;
        p.y += p.vy;
        p.tw += p.ts;
        if (p.x < -10) p.x = w + 10;
        if (p.x > w + 10) p.x = -10;
        if (p.y < -10) p.y = h + 10;
        if (p.y > h + 10) p.y = -10;
        const alpha = p.a * (0.65 + 0.35 * Math.sin(p.tw));
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(168, 85, 247, ${alpha.toFixed(3)})`;
        ctx.fill();
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  /* ---------------- Chart.js defaults ---------------- */

  function applyChartDefaults() {
    if (typeof Chart === "undefined") return;
    Chart.defaults.color = palette.textDim;
    Chart.defaults.font.family =
      "Inter, Geist, system-ui, -apple-system, 'Segoe UI', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.color = palette.text;
    Chart.defaults.plugins.tooltip.backgroundColor = "#171324";
    Chart.defaults.plugins.tooltip.titleColor = palette.text;
    Chart.defaults.plugins.tooltip.bodyColor = palette.textDim;
    Chart.defaults.plugins.tooltip.borderColor = palette.border;
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.scale.grid.color = "rgba(42, 36, 64, 0.5)";
    Chart.defaults.scale.grid.borderColor = palette.border;
    Chart.defaults.animation.duration = prefersReducedMotion ? 0 : 700;
    Chart.defaults.animation.easing = "easeOutQuart";
  }

  function violetGradient(ctx, chartArea, alphaTop = 0.5, alphaBottom = 0.02) {
    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    gradient.addColorStop(0, `rgba(139, 92, 246, ${alphaTop})`);
    gradient.addColorStop(1, `rgba(139, 92, 246, ${alphaBottom})`);
    return gradient;
  }

  return {
    API_BASE,
    palette,
    prefersReducedMotion,
    getJSON,
    renderLoading,
    renderError,
    initReveal,
    animateCount,
    formatCompact,
    renderHeader,
    renderLimitationsBanner,
    escapeHTML,
    applyChartDefaults,
    violetGradient,
    initPageTransition,
    initBackground,
  };
})();

SMI.initPageTransition();
SMI.initBackground();
