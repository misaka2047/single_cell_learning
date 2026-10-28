(() => {
  "use strict";

  const COURSE = Array.isArray(window.COURSE) ? window.COURSE : [];
  const KEY = "scrna-course-progress-v1";
  const body = document.body;
  const base = body.dataset.base || "";
  const currentSlug = body.dataset.slug || "";

  const readState = () => {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : {};
    } catch (_) {
      return {};
    }
  };

  const writeState = (state) => {
    try {
      localStorage.setItem(KEY, JSON.stringify(state));
    } catch (_) {
      /* file:// or private mode: progress is best-effort */
    }
  };

  let state = readState();

  const isDone = (slug) => Boolean(state[slug]);
  const doneCount = () => COURSE.filter((c) => isDone(c.slug)).length;

  const updateProgress = () => {
    const count = doneCount();
    const total = COURSE.length || 1;
    const pct = Math.round((count / total) * 100);

    document.querySelectorAll("#progress-fill").forEach((el) => {
      el.style.width = `${pct}%`;
    });
    document.querySelectorAll("#progress-text").forEach((el) => {
      el.textContent = `${count} / ${COURSE.length}`;
    });
    document.querySelectorAll("#topbar-progress").forEach((el) => {
      el.textContent = `${pct}% 已完成`;
    });

    document.querySelectorAll(".chapter-link").forEach((a) => {
      a.classList.toggle("done", isDone(a.dataset.slug));
    });

    document.querySelectorAll(".course-card").forEach((card) => {
      const slug = card.dataset.slug;
      const done = isDone(slug);
      card.classList.toggle("done", done);
      const label = card.querySelector(".course-state");
      if (label) label.textContent = done ? "已完成 ✓" : "未开始";
    });

    const btn = document.getElementById("mark-complete");
    if (btn) {
      const done = isDone(currentSlug);
      btn.textContent = done ? "已完成，点击取消" : "标记本章完成";
      btn.setAttribute("aria-pressed", done ? "true" : "false");
      btn.classList.toggle("btn-primary", !done);
      btn.classList.toggle("btn-ghost", done);
    }
  };

  const toggleCurrent = () => {
    if (!currentSlug) return;
    state[currentSlug] = !state[currentSlug];
    if (!state[currentSlug]) delete state[currentSlug];
    writeState(state);
    updateProgress();
  };

  const initProgress = () => {
    const btn = document.getElementById("mark-complete");
    if (btn) btn.addEventListener("click", toggleCurrent);
    updateProgress();
  };

  const initSidebar = () => {
    const menu = document.getElementById("menu-btn");
    const overlay = document.getElementById("sidebar-overlay");
    if (!menu) return;
    const close = () => {
      body.classList.remove("sidebar-open");
      menu.setAttribute("aria-expanded", "false");
    };
    menu.addEventListener("click", () => {
      const open = body.classList.toggle("sidebar-open");
      menu.setAttribute("aria-expanded", open ? "true" : "false");
    });
    if (overlay) overlay.addEventListener("click", close);
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
    document.querySelectorAll(".chapter-link").forEach((a) => {
      a.addEventListener("click", close);
    });
  };

  const esc = (s) =>
    String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");

  const initSearch = () => {
    const input = document.getElementById("site-search");
    const panel = document.getElementById("search-results");
    if (!input || !panel) return;

    const render = (query) => {
      const q = query.trim().toLowerCase();
      if (!q) {
        panel.hidden = true;
        panel.innerHTML = "";
        return;
      }
      const terms = q.split(/\s+/).filter(Boolean);
      const hits = COURSE.filter((c) => {
        const hay = [c.num, c.title, c.short, c.keywords, c.duration]
          .join(" ")
          .toLowerCase();
        return terms.every((t) => hay.includes(t));
      }).slice(0, 8);

      if (!hits.length) {
        panel.innerHTML = `<div class="search-empty">没有匹配章节，试试“QC”“pseudobulk”“注释”</div>`;
        panel.hidden = false;
        return;
      }
      panel.innerHTML = hits
        .map(
          (c) =>
            `<a class="search-item" href="${base}chapters/${c.slug}.html">` +
            `<b>${esc(c.num)}. ${esc(c.title)}</b>` +
            `<span>${esc(c.short)}</span></a>`
        )
        .join("");
      panel.hidden = false;
    };

    input.addEventListener("input", (e) => render(e.target.value));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        panel.hidden = true;
        input.blur();
      }
      if (e.key === "Enter") {
        const first = panel.querySelector("a.search-item");
        if (first) window.location.href = first.getAttribute("href");
      }
    });
    document.addEventListener("click", (e) => {
      if (!panel.contains(e.target) && e.target !== input) panel.hidden = true;
    });
  };

  const initCopy = () => {
    document.querySelectorAll(".prose pre").forEach((pre) => {
      if (pre.querySelector(".copy-btn")) return;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "copy-btn";
      btn.textContent = "复制";
      btn.setAttribute("aria-label", "复制代码");
      btn.addEventListener("click", async () => {
        const code = pre.querySelector("code");
        const text = (code || pre).innerText;
        try {
          if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text);
          } else {
            const ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed";
            ta.style.opacity = "0";
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
          }
          btn.textContent = "已复制";
          setTimeout(() => (btn.textContent = "复制"), 1400);
        } catch (_) {
          btn.textContent = "复制失败";
          setTimeout(() => (btn.textContent = "复制"), 1400);
        }
      });
      pre.appendChild(btn);
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    initProgress();
    initSidebar();
    initSearch();
    initCopy();
  });
})();
