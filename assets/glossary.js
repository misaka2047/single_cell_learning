(() => {
  "use strict";

  const GLOSSARY = Array.isArray(window.GLOSSARY) ? window.GLOSSARY : [];
  if (!GLOSSARY.length) return;

  const body = document.body;
  const isGlossaryPage = body.dataset.glossaryPage === "true";

  const entryByTerm = new Map();
  const entryByKey = new Map();
  for (const entry of GLOSSARY) {
    entryByTerm.set(entry.term, entry);
    entryByKey.set(entry.term.toLowerCase(), entry);
    for (const alias of entry.aliases || []) {
      entryByKey.set(String(alias).toLowerCase(), entry);
    }
  }

  /* ------------------------------------------------------------------ */
  /* Glossary page: simple client-side filter                            */
  /* ------------------------------------------------------------------ */
  const initGlossaryFilter = () => {
    const input = document.getElementById("glossary-search");
    if (!input) return;
    const entries = Array.from(document.querySelectorAll(".gloss-entry"));
    const count = document.getElementById("glossary-count");
    const sections = Array.from(document.querySelectorAll(".glossary-cat"));

    const apply = () => {
      const q = input.value.trim().toLowerCase();
      let visible = 0;
      entries.forEach((el) => {
        const hay = (el.dataset.keywords || el.textContent || "").toLowerCase();
        const hit = !q || hay.includes(q);
        el.hidden = !hit;
        if (hit) visible += 1;
      });
      sections.forEach((sec) => {
        sec.hidden = !sec.querySelector(".gloss-entry:not([hidden])");
      });
      if (count) {
        count.textContent = q ? `${visible} 个匹配` : `${GLOSSARY.length} 个词条`;
      }
    };

    input.addEventListener("input", apply);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        input.value = "";
        apply();
      }
    });
  };

  if (isGlossaryPage) {
    document.addEventListener("DOMContentLoaded", initGlossaryFilter);
    return;
  }

  /* ------------------------------------------------------------------ */
  /* Chapter pages: wrap first occurrence of each term, show a tooltip    */
  /* ------------------------------------------------------------------ */
  const escapeRegExp = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const keys = Array.from(entryByKey.keys()).sort((a, b) => b.length - a.length);
  const pattern = new RegExp(
    `(?<![A-Za-z0-9])(${keys.map(escapeRegExp).join("|")})(?![A-Za-z0-9])`,
    "gi"
  );

  const seenTerms = new Set();

  const makeSpan = (matched, entry) => {
    const span = document.createElement("span");
    span.className = "gloss";
    span.tabIndex = 0;
    span.setAttribute("role", "note");
    span.dataset.glossTerm = entry.term;
    span.setAttribute("aria-label", `${entry.term}：${entry.definition}`);
    span.textContent = matched;
    return span;
  };

  const wrapTextNode = (node) => {
    const text = node.nodeValue || "";
    if (!text.trim()) return;
    pattern.lastIndex = 0;
    let match;
    let last = 0;
    let changed = false;
    const frag = document.createDocumentFragment();

    while ((match = pattern.exec(text)) !== null) {
      const matched = match[1];
      const entry = entryByKey.get(matched.toLowerCase());
      if (!entry) continue;
      if (seenTerms.has(entry.term)) continue;

      const start = match.index;
      const end = start + matched.length;
      if (start > last) {
        frag.appendChild(document.createTextNode(text.slice(last, start)));
      }
      frag.appendChild(makeSpan(matched, entry));
      seenTerms.add(entry.term);
      last = end;
      changed = true;
    }

    if (!changed) return;
    if (last < text.length) {
      frag.appendChild(document.createTextNode(text.slice(last)));
    }
    node.parentNode.replaceChild(frag, node);
  };

  const collectTextNodes = () => {
    const roots = Array.from(
      document.querySelectorAll(".prose, .chapter-lead")
    );
    const nodes = [];
    for (const root of roots) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode(node) {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          if (!node.nodeValue || !node.nodeValue.trim()) {
            return NodeFilter.FILTER_REJECT;
          }
          if (
            parent.closest(
              "code, pre, a, h1, h2, h3, h4, h5, h6, summary, button, .gloss, .no-gloss"
            )
          ) {
            return NodeFilter.FILTER_REJECT;
          }
          return NodeFilter.FILTER_ACCEPT;
        },
      });
      while (walker.nextNode()) nodes.push(walker.currentNode);
    }
    return nodes;
  };

  const initTooltip = () => {
    const nodes = collectTextNodes();
    nodes.forEach(wrapTextNode);
    if (!document.querySelector(".gloss")) return;

    const tip = document.createElement("div");
    tip.className = "gloss-tip";
    tip.setAttribute("role", "tooltip");
    tip.hidden = true;
    document.body.appendChild(tip);

    let active = null;
    let showTimer = null;
    let hideTimer = null;

    const position = (el) => {
      const r = el.getBoundingClientRect();
      const pad = 12;
      tip.style.left = "0px";
      tip.style.top = "0px";
      const tw = tip.offsetWidth;
      const th = tip.offsetHeight;
      let left = Math.min(Math.max(pad, r.left), window.innerWidth - tw - pad);
      let top = r.bottom + 8;
      if (top + th > window.innerHeight - pad) {
        top = r.top - th - 8;
      }
      tip.style.left = `${Math.max(pad, left)}px`;
      tip.style.top = `${Math.max(pad, top)}px`;
    };

    const render = (entry) => {
      tip.replaceChildren();
      const title = document.createElement("b");
      title.textContent = entry.term;
      const text = document.createElement("p");
      text.textContent = entry.definition;
      tip.append(title, text);
    };

    const show = (el) => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
      const entry = entryByTerm.get(el.dataset.glossTerm);
      if (!entry) return;
      active = el;
      render(entry);
      tip.hidden = false;
      requestAnimationFrame(() => position(el));
    };

    const hide = () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
      active = null;
      tip.hidden = true;
    };

    const scheduleShow = (el) => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
      showTimer = setTimeout(() => show(el), 70);
    };

    const scheduleHide = () => {
      clearTimeout(showTimer);
      clearTimeout(hideTimer);
      hideTimer = setTimeout(hide, 120);
    };

    document.addEventListener("mouseover", (e) => {
      const el = e.target.closest && e.target.closest(".gloss");
      if (el) scheduleShow(el);
    });
    document.addEventListener("mouseout", (e) => {
      const el = e.target.closest && e.target.closest(".gloss");
      if (!el) return;
      const related = e.relatedTarget;
      if (related && el.contains(related)) return;
      scheduleHide();
    });
    document.addEventListener("focusin", (e) => {
      const el = e.target.closest && e.target.closest(".gloss");
      if (el) show(el);
    });
    document.addEventListener("focusout", (e) => {
      const el = e.target.closest && e.target.closest(".gloss");
      if (el) scheduleHide();
    });
    document.addEventListener("click", (e) => {
      const el = e.target.closest && e.target.closest(".gloss");
      if (!el) {
        if (active) hide();
        return;
      }
      e.preventDefault();
      show(el);
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") hide();
    });
    window.addEventListener("scroll", () => {
      if (active) hide();
    }, true);
    window.addEventListener("resize", () => {
      if (active) hide();
    });
  };

  document.addEventListener("DOMContentLoaded", initTooltip);
})();
