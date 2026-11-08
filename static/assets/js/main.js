/*!
 * Site behaviour. No dependencies, no build step.
 * Organised as small independent modules; each checks for its own DOM
 * before doing anything, so this file is safe to include on every page.
 */
(function () {
  "use strict";

  var root = document.documentElement;
  var ROOT = root.getAttribute("data-root") || "./";
  var prefersReduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------------
   * Theme toggle (dark / light / system), persisted in localStorage
   * ------------------------------------------------------------------- */
  (function themeModule() {
    var toggle = document.getElementById("theme-toggle");
    var panel = document.getElementById("theme-panel");
    if (!toggle || !panel) return;

    var mql = matchMedia("(prefers-color-scheme: light)");

    function apply(pref) {
      var resolved = pref === "system" ? (mql.matches ? "light" : "dark") : pref;
      root.setAttribute("data-theme", resolved === "light" ? "light" : "dark");
      root.setAttribute("data-theme-pref", pref);
      panel.querySelectorAll("[data-theme-set]").forEach(function (btn) {
        var active = btn.getAttribute("data-theme-set") === pref;
        btn.setAttribute("aria-pressed", String(active));
      });
      var meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", resolved === "dark" ? "#08090d" : "#fafbfd");
    }

    function store(pref) {
      try { localStorage.setItem("theme", pref); } catch (e) {}
    }

    apply(root.getAttribute("data-theme-pref") || "light");

    mql.addEventListener("change", function () {
      if ((root.getAttribute("data-theme-pref") || "light") === "system") apply("system");
    });

    function closePanel() {
      panel.hidden = true;
      toggle.setAttribute("aria-expanded", "false");
    }
    toggle.addEventListener("click", function (e) {
      e.stopPropagation();
      var willOpen = panel.hidden;
      panel.hidden = !willOpen;
      toggle.setAttribute("aria-expanded", String(willOpen));
      if (willOpen) {
        var current = panel.querySelector('[aria-pressed="true"]') || panel.querySelector("button");
        if (current) current.focus();
      }
    });
    panel.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-theme-set]");
      if (!btn) return;
      var pref = btn.getAttribute("data-theme-set");
      apply(pref);
      store(pref);
      closePanel();
      toggle.focus();
    });
    document.addEventListener("click", function (e) {
      if (!panel.hidden && !panel.contains(e.target) && e.target !== toggle) closePanel();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) { closePanel(); toggle.focus(); }
    });
  })();

  /* ---------------------------------------------------------------------
   * Sticky header: translucent + blurred once the page scrolls
   * ------------------------------------------------------------------- */
  (function headerModule() {
    var header = document.getElementById("site-header");
    if (!header) return;
    var sentinel = document.getElementById("top-sentinel");
    if (sentinel && "IntersectionObserver" in window) {
      var io = new IntersectionObserver(function (entries) {
        header.classList.toggle("is-scrolled", !entries[0].isIntersecting);
      });
      io.observe(sentinel);
    } else {
      var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 4); };
      document.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }
  })();

  /* ---------------------------------------------------------------------
   * Mobile menu
   * ------------------------------------------------------------------- */
  (function navModule() {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.getElementById("site-nav");
    var header = document.getElementById("site-header");
    if (!toggle || !nav) return;
    toggle.addEventListener("click", function () {
      var open = !nav.classList.contains("is-open");
      nav.classList.toggle("is-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      if (header) header.classList.toggle("menu-open", open);
      document.body.style.overflow = open ? "hidden" : "";
    });
    nav.addEventListener("click", function (e) {
      if (e.target.closest("a")) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Open menu");
        if (header) header.classList.remove("menu-open");
        document.body.style.overflow = "";
      }
    });
    matchMedia("(min-width: 861px)").addEventListener("change", function (e) {
      if (e.matches) {
        nav.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      }
    });
  })();

  /* ---------------------------------------------------------------------
   * Category filter chips (listing pages + projects)
   * ------------------------------------------------------------------- */
  (function filterModule() {
    var group = document.querySelector("[data-filter-group]");
    var list = document.querySelector("[data-filter-list]");
    if (!group || !list) return;
    var empty = document.querySelector("[data-filter-empty]");
    var items = Array.prototype.slice.call(list.children);

    function apply(filter) {
      var visible = 0;
      items.forEach(function (item) {
        var cats = (item.getAttribute("data-category") || "").split(" ");
        var show = filter === "all" || cats.indexOf(filter) !== -1;
        item.hidden = !show;
        if (show) visible++;
      });
      if (empty) empty.hidden = visible !== 0;
    }

    group.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-filter]");
      if (!btn) return;
      group.querySelectorAll(".chip").forEach(function (c) {
        c.classList.toggle("is-active", c === btn);
        c.setAttribute("aria-pressed", String(c === btn));
      });
      apply(btn.getAttribute("data-filter"));
    });

    document.addEventListener("click", function (e) {
      if (e.target.closest("[data-filter-reset]")) {
        var allBtn = group.querySelector('[data-filter="all"]');
        if (allBtn) allBtn.click();
      }
    });
  })();

  /* ---------------------------------------------------------------------
   * Reveal-on-scroll (subtle fade/rise, skipped for reduced motion)
   * ------------------------------------------------------------------- */
  (function revealModule() {
    var targets = document.querySelectorAll(".reveal");
    if (!targets.length || prefersReduced || !("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -8% 0px" }
    );
    targets.forEach(function (t) { io.observe(t); });
  })();

  /* ---------------------------------------------------------------------
   * Copy-to-clipboard: code blocks + the RSS URL field
   * ------------------------------------------------------------------- */
  (function copyModule() {
    function flash(btn, label, revertLabel) {
      var span = btn.querySelector("span:not(.i)") || btn;
      var original = span.textContent;
      btn.classList.add("is-copied");
      span.textContent = label;
      setTimeout(function () {
        btn.classList.remove("is-copied");
        span.textContent = revertLabel || original;
      }, 1800);
    }
    function copy(text) {
      if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text).catch(function () { fallbackCopy(text); });
      }
      fallbackCopy(text);
      return Promise.resolve();
    }
    function fallbackCopy(text) {
      var ta = document.createElement("textarea");
      ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); } catch (e) {}
      document.body.removeChild(ta);
    }
    document.addEventListener("click", function (e) {
      var codeBtn = e.target.closest(".code-copy");
      if (codeBtn) {
        var code = codeBtn.closest(".code-block").querySelector("code");
        copy(code.textContent).finally(function () { flash(codeBtn, "Copied!", "Copy"); });
        return;
      }
      var copyBtn = e.target.closest("[data-copy-btn]");
      if (copyBtn) {
        var src = document.querySelector("[data-copy-source]");
        if (src) copy(src.value).finally(function () { flash(copyBtn, "Copied!", "Copy"); });
      }
    });
  })();

  /* ---------------------------------------------------------------------
   * Article page: reading progress bar + table-of-contents scroll-spy
   * ------------------------------------------------------------------- */
  (function articleModule() {
    var prose = document.querySelector(".prose");
    if (!prose) return;

    var bar = document.querySelector(".reading-progress > span");
    if (bar) {
      var update = function () {
        var rect = prose.getBoundingClientRect();
        var total = rect.height - window.innerHeight * 0.6;
        var passed = -rect.top;
        var ratio = total > 0 ? Math.min(1, Math.max(0, passed / total)) : 0;
        bar.style.transform = "scaleX(" + ratio.toFixed(4) + ")";
      };
      document.addEventListener("scroll", update, { passive: true });
      window.addEventListener("resize", update);
      update();
    }

    var tocLinks = document.querySelectorAll(".toc__list a");
    if (tocLinks.length && "IntersectionObserver" in window) {
      var map = {};
      tocLinks.forEach(function (a) { map[a.getAttribute("href").slice(1)] = a; });
      var current = null;
      var headingIO = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            var link = map[entry.target.id];
            if (!link) return;
            if (entry.isIntersecting) {
              if (current) current.classList.remove("is-active");
              current = link;
              current.classList.add("is-active");
            }
          });
        },
        { rootMargin: "-15% 0px -70% 0px", threshold: 0 }
      );
      prose.querySelectorAll("h2[id], h3[id]").forEach(function (h) { headingIO.observe(h); });
    }
  })();

  /* ---------------------------------------------------------------------
   * Lightbox: click a project screenshot thumbnail to view it full-size.
   * ------------------------------------------------------------------- */
  (function lightboxModule() {
    var dialog = document.getElementById("lightbox-dialog");
    var img = document.getElementById("lightbox-img");
    var caption = document.getElementById("lightbox-caption");
    if (!dialog || !img) return;

    function open(src, cap) {
      img.src = src;
      img.alt = cap || "";
      caption.textContent = cap || "";
      caption.hidden = !cap;
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
    }
    function close() {
      if (typeof dialog.close === "function" && dialog.open) dialog.close();
      else dialog.removeAttribute("open");
    }

    document.addEventListener("click", function (e) {
      var btn = e.target.closest("[data-lightbox]");
      if (btn) { open(btn.getAttribute("data-src"), btn.getAttribute("data-caption")); return; }
      if (e.target.closest("[data-lightbox-close]")) close();
      if (e.target === dialog) close();
    });
    dialog.addEventListener("cancel", function (e) { e.preventDefault(); close(); });
    dialog.addEventListener("close", function () { img.src = ""; });
  })();

  /* ---------------------------------------------------------------------
   * Math: load KaTeX only on pages that contain a formula, then render.
   * Content is stashed as escaped text in .math elements at build time.
   * ------------------------------------------------------------------- */
  (function mathModule() {
    var host = document.querySelector(".prose[data-katex]");
    if (!host) return;
    var base = host.getAttribute("data-katex");
    var cssLink = document.createElement("link");
    cssLink.rel = "stylesheet";
    cssLink.href = base + "/katex.min.css";
    document.head.appendChild(cssLink);

    var script = document.createElement("script");
    script.src = base + "/katex.min.js";
    script.onload = function () {
      host.querySelectorAll(".math").forEach(function (el) {
        var display = el.classList.contains("math-display");
        try {
          window.katex.render(el.textContent, el, { displayMode: display, throwOnError: false, strict: "ignore" });
          el.classList.add("is-rendered");
        } catch (e) { /* leave the raw text visible */ }
      });
    };
    document.body.appendChild(script);
  })();

  /* ---------------------------------------------------------------------
   * Search: fetch /search.json once, then do a fast client-side match.
   * Opens with the search button, "/" or Ctrl+K / Cmd+K.
   * ------------------------------------------------------------------- */
  (function searchModule() {
    var dialog = document.getElementById("search-dialog");
    var input = document.getElementById("search-input");
    var results = document.getElementById("search-results");
    var status = document.getElementById("search-status");
    if (!dialog || !input) return;

    var index = null, indexPromise = null, activeIndex = -1, currentItems = [];

    function loadIndex() {
      if (indexPromise) return indexPromise;
      status.textContent = "Loading index\u2026";
      indexPromise = fetch(ROOT + "search.json")
        .then(function (r) { return r.json(); })
        .then(function (data) { index = data; return data; })
        .catch(function () { status.textContent = "Search index failed to load."; return []; });
      return indexPromise;
    }

    function escapeHtml(s) {
      return s.replace(/[&<>"']/g, function (c) {
        return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
      });
    }
    function escapeReg(s) { return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
    function highlight(text, terms) {
      if (!terms.length) return escapeHtml(text);
      var re = new RegExp("(" + terms.map(escapeReg).join("|") + ")", "ig");
      return escapeHtml(text).replace(re, "<mark>$1</mark>");
    }
    function snippet(text, terms, radius) {
      radius = radius || 70;
      var lower = text.toLowerCase();
      var pos = -1;
      for (var i = 0; i < terms.length; i++) {
        var p = lower.indexOf(terms[i]);
        if (p !== -1 && (pos === -1 || p < pos)) pos = p;
      }
      if (pos === -1) return text.slice(0, radius * 2) + (text.length > radius * 2 ? "\u2026" : "");
      var start = Math.max(0, pos - radius);
      var end = Math.min(text.length, pos + radius);
      return (start > 0 ? "\u2026" : "") + text.slice(start, end) + (end < text.length ? "\u2026" : "");
    }

    function score(item, terms) {
      var hay = { t: item.t.toLowerCase(), d: item.d.toLowerCase(), c: item.c.toLowerCase(), g: item.g.join(" ").toLowerCase(), x: item.x.toLowerCase() };
      var s = 0;
      terms.forEach(function (term) {
        if (hay.t.indexOf(term) !== -1) s += hay.t.indexOf(term) === 0 ? 12 : 8;
        if (hay.g.indexOf(term) !== -1) s += 5;
        if (hay.c.indexOf(term) !== -1) s += 4;
        if (hay.d.indexOf(term) !== -1) s += 3;
        if (hay.x.indexOf(term) !== -1) s += 1;
      });
      var allPresent = terms.every(function (term) {
        return hay.t.indexOf(term) !== -1 || hay.d.indexOf(term) !== -1 || hay.g.indexOf(term) !== -1 || hay.x.indexOf(term) !== -1;
      });
      return allPresent ? s : 0;
    }

    function render(items, terms) {
      currentItems = items;
      activeIndex = items.length ? 0 : -1;
      results.innerHTML = items
        .map(function (item, i) {
          return (
            '<li role="option" id="sr-' + i + '"' + (i === 0 ? ' class="is-active"' : "") + '>' +
            '<a class="search__item" href="' + ROOT + item.u + '" tabindex="-1">' +
            '<span class="search__title">' + highlight(item.t, terms) + "</span>" +
            '<span class="search__meta"><span>' + escapeHtml(item.c) + "</span><span>" + escapeHtml(item.dt) + "</span><span>" + item.r + " min read</span></span>" +
            '<span class="search__snippet">' + highlight(snippet(item.x, terms), terms) + "</span>" +
            "</a></li>"
          );
        })
        .join("");
      input.setAttribute("aria-activedescendant", items.length ? "sr-0" : "");
    }

    function runQuery(q) {
      q = q.trim();
      if (!q) {
        results.innerHTML = "";
        status.textContent = index ? "Type to search " + index.length + " articles." : "";
        input.setAttribute("aria-activedescendant", "");
        return;
      }
      var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
      var scored = (index || [])
        .map(function (item) { return { item: item, s: score(item, terms) }; })
        .filter(function (r) { return r.s > 0; })
        .sort(function (a, b) { return b.s - a.s; })
        .slice(0, 20)
        .map(function (r) { return r.item; });

      if (!scored.length) {
        status.textContent = "No matches found.";
        results.innerHTML =
          '<li class="search__empty-item" role="presentation">' +
          '<div class="search__empty-card">' +
          '<div class="search__empty-icon">' +
          '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/><path d="M9 11h4"/></svg>' +
          '</div>' +
          '<p class="search__empty-title">No results for \u201c' + escapeHtml(q) + '\u201d</p>' +
          '<p class="search__empty-tip">Try searching for keywords like <strong>Flutter</strong>, <strong>BLoC</strong>, or <strong>Stripe</strong>.</p>' +
          '</div></li>';
        input.setAttribute("aria-activedescendant", "");
        return;
      }

      status.textContent = scored.length + " result" + (scored.length === 1 ? "" : "s");
      render(scored, terms);
    }

    function moveActive(delta) {
      if (!currentItems.length) return;
      activeIndex = (activeIndex + delta + currentItems.length) % currentItems.length;
      results.querySelectorAll("li").forEach(function (li, i) { li.classList.toggle("is-active", i === activeIndex); });
      input.setAttribute("aria-activedescendant", "sr-" + activeIndex);
      var li = results.children[activeIndex];
      if (li) li.scrollIntoView({ block: "nearest" });
    }

    function open() {
      loadIndex().then(function () { runQuery(input.value); });
      if (typeof dialog.showModal === "function") dialog.showModal();
      else dialog.setAttribute("open", "");
      setTimeout(function () { input.focus(); input.select(); }, 10);
    }
    function close() {
      if (typeof dialog.close === "function" && dialog.open) dialog.close();
      else dialog.removeAttribute("open");
    }

    document.addEventListener("click", function (e) {
      if (e.target.closest("[data-search-open]")) { e.preventDefault(); open(); }
      if (e.target.closest("[data-search-close]")) close();
      if (e.target === dialog) close(); // backdrop click on <dialog> lands on the dialog itself
    });
    document.addEventListener("keydown", function (e) {
      var mod = e.ctrlKey || e.metaKey;
      if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); dialog.open ? close() : open(); return; }
      if (e.key === "/" && !dialog.open && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
        e.preventDefault(); open();
      }
    });
    dialog.addEventListener("cancel", function (e) { e.preventDefault(); close(); });
    dialog.addEventListener("close", function () { results.innerHTML = ""; input.value = ""; status.textContent = ""; });

    input.addEventListener("input", function () { runQuery(input.value); });
    input.addEventListener("keydown", function (e) {
      if (e.key === "ArrowDown") { e.preventDefault(); moveActive(1); }
      else if (e.key === "ArrowUp") { e.preventDefault(); moveActive(-1); }
      else if (e.key === "Enter") {
        e.preventDefault();
        var link = results.querySelectorAll("a")[activeIndex];
        if (link) window.location.href = link.getAttribute("href");
      }
    });

    var kbdKey = navigator.platform && /Mac|iPhone|iPad/.test(navigator.platform) ? "\u2318 K" : "Ctrl K";
    document.querySelectorAll("[data-kbd]").forEach(function (el) { el.textContent = kbdKey; });
  })();
})();
