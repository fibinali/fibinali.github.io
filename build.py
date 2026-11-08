#!/usr/bin/env python3
"""
Static site generator for this blog.

    python build.py                 # build into ./dist
    python build.py --serve         # build, then preview at http://localhost:8000
    python build.py --site-url https://me.github.io/my-repo   # override site.yml url

Content lives in ./content, templates in ./templates, static assets in ./static.
Every internal link in the generated HTML is *relative*, so the output works
unchanged at https://USER.github.io/, at https://USER.github.io/REPO/, on a
custom domain, or when opened from a local folder / dev server.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import html
import http.server
import json
import math
import random
import re
import shutil
import socketserver
import sys
from email.utils import format_datetime
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown.extensions import Extension
from markdown.extensions.toc import TocExtension
from markdown.preprocessors import Preprocessor
from markupsafe import Markup
from pygments import highlight as pyg_highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name
from pygments.util import ClassNotFound

BASE = Path(__file__).resolve().parent
CONTENT = BASE / "content"
TEMPLATES = BASE / "templates"
STATIC = BASE / "static"

ROOT_TOKEN = "@@ROOT@@"  # replaced by the correct relative prefix at render time
WORDS_PER_MINUTE = 210

# ───────────────────────────── icons ─────────────────────────────

ICONS = {
    "search": '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6 6 6M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>',
    "moon": '<path d="M20.5 13.2A8.5 8.5 0 0 1 10.8 3.5a8.5 8.5 0 1 0 9.7 9.7z"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "calendar": '<rect x="3.5" y="5" width="17" height="15.5" rx="2.5"/><path d="M8 3v4M16 3v4M3.5 10h17"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "copy": '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
    "external": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    "rss": '<path d="M5 12a7 7 0 0 1 7 7M5 5a14 14 0 0 1 14 14"/><circle cx="6" cy="18" r="1.3"/>',
    "shield": '<path d="M12 3 5 6v5.5c0 4.4 3 7.9 7 9.5 4-1.6 7-5.1 7-9.5V6l-7-3z"/>',
    "shield-check": '<path d="M12 3 5 6v5.5c0 4.4 3 7.9 7 9.5 4-1.6 7-5.1 7-9.5V6l-7-3z"/><path d="m9 12 2.2 2.2L15.5 10"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/><path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>',
    "code": '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 6l-3 12"/>',
    "flask": '<path d="M9 3h6M10 3v6l-5.4 9.3A1.6 1.6 0 0 0 6 21h12a1.6 1.6 0 0 0 1.4-2.7L14 9V3"/><path d="M7.5 15h9"/>',
    "terminal": '<path d="m4 6 6 6-6 6M13 19h7"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.6v.01"/>',
    "alert": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5M12 16v.01"/>',
    "triangle": '<path d="M12 3.5 21.5 20h-19L12 3.5z"/><path d="M12 10v4.5M12 17.5v.01"/>',
    "bug": '<path d="M9 8V7a3 3 0 0 1 6 0v1M7.5 8h9v6a4.5 4.5 0 0 1-9 0V8zM3 12.5h4.5M16.5 12.5H21M4.5 6.5 7.5 9M19.5 6.5 16.5 9M4.5 19l3-2.3M19.5 19l-3-2.3M12 11v9"/>',
    "inbox": '<path d="M4 13h4.3l1.4 2.8h4.6l1.4-2.8H20"/><path d="M6 5.5h12L20 13v4.5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V13L6 5.5z"/>',
    "bulb": '<path d="M9.5 18h5M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/>',
    "layers": '<path d="m12 3 9 5-9 5-9-5 9-5zM3 13l9 5 9-5"/>',
    "tag": '<path d="M3.5 12.5V4.5h8l9 9-8 8-9-9z"/><circle cx="8" cy="9" r="1.2"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "image": '<rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/>',
    "github": "M12 .3a12 12 0 0 0-3.8 23.4c.6.1.8-.3.8-.6v-2c-3.3.7-4-1.6-4-1.6-.6-1.4-1.4-1.8-1.4-1.8-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.8 1.3 3.5 1 0-.8.4-1.3.7-1.6-2.7-.3-5.5-1.3-5.5-6 0-1.2.5-2.3 1.3-3.1-.2-.4-.6-1.6 0-3.2 0 0 1-.3 3.4 1.2a11.5 11.5 0 0 1 6 0c2.3-1.5 3.3-1.2 3.3-1.2.7 1.6.3 2.8.2 3.2.8.8 1.3 1.9 1.3 3.1 0 4.6-2.8 5.6-5.5 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .3",
    "linkedin": "M20.4 20.5h-3.6v-5.6c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9v5.7H9.4V9h3.4v1.6c.5-.9 1.6-1.8 3.4-1.8 3.6 0 4.3 2.4 4.3 5.5v6.2zM5.3 7.4a2.1 2.1 0 1 1 0-4.1 2.1 2.1 0 0 1 0 4.1zM7.1 20.5H3.6V9h3.5v11.5zM22.2 0H1.8C.8 0 0 .8 0 1.7v20.6c0 .9.8 1.7 1.8 1.7h20.4c1 0 1.8-.8 1.8-1.7V1.7C24 .8 23.2 0 22.2 0z",
}
BRAND_ICONS = {"github", "linkedin"}


def icon(name: str, size: int = 18, cls: str = "") -> Markup:
    body = ICONS[name]
    c = f' class="i {cls}"' if cls else ' class="i"'
    if name in BRAND_ICONS:
        return Markup(
            f'<svg{c} width="{size}" height="{size}" viewBox="0 0 24 24" fill="currentColor" '
            f'aria-hidden="true" focusable="false"><path d="{body}"/></svg>'
        )
    return Markup(
        f'<svg{c} width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" '
        f'focusable="false">{body}</svg>'
    )


# ───────────────────────── markdown extensions ─────────────────────────
# Callouts:   ::: security-note            (optional custom title after the type)
#             Only test systems you own.
#             :::
# Math:       $inline$   and   $$ display $$   (rendered by KaTeX only on pages that use it)

CALLOUTS = {
    "note": ("Note", "info"),
    "important": ("Important", "alert"),
    "warning": ("Warning", "triangle"),
    "security-note": ("Security Note", "shield"),
    "example": ("Example", "flask"),
    "command": ("Command", "terminal"),
    "vulnerability": ("Vulnerability", "bug"),
    "mitigation": ("Mitigation", "shield-check"),
    "tip": ("Tip", "bulb"),
}
CALLOUT_OPEN = re.compile(r"^:::\s*([a-z-]+)(?:\s+(.+?))?\s*$")


class CalloutPreprocessor(Preprocessor):
    def run(self, lines):
        out, in_fence, is_open = [], False, False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(("```", "~~~")):
                in_fence = not in_fence
            if not in_fence:
                m = CALLOUT_OPEN.match(line)
                if m and not is_open and m.group(1) in CALLOUTS:
                    kind = m.group(1)
                    default_title, icon_name = CALLOUTS[kind]
                    title = html.escape(m.group(2) or default_title)
                    out += [
                        "",
                        f'<div class="callout callout--{kind}" role="note" markdown="1">',
                        f'<p class="callout__title">{icon(icon_name, 16)}<span>{title}</span></p>',
                        "",
                    ]
                    is_open = True
                    continue
                if is_open and stripped == ":::":
                    out += ["", "</div>", ""]
                    is_open = False
                    continue
            out.append(line)
        if is_open:
            raise ValueError("Unclosed ::: callout block")
        return out


MATH_RE = re.compile(
    r"(?P<code>`+[^`\n]*?`+)"
    r"|\$\$(?P<block>.+?)\$\$"
    r"|(?<![\\$\w])\$(?P<inline>(?!\s)[^$\n]+?(?<!\s))\$(?![\w$])",
    re.S,
)


class MathPreprocessor(Preprocessor):
    """Stash $…$ / $$…$$ so Markdown doesn't mangle underscores and backslashes."""

    def run(self, lines):
        def repl(m):
            if m.group("code"):
                return m.group(0)
            if m.group("block") is not None:
                tex = html.escape(m.group("block").strip(), quote=False)
                return self.md.htmlStash.store(f'<div class="math math-display">{tex}</div>')
            tex = html.escape(m.group("inline"), quote=False)
            return self.md.htmlStash.store(f'<span class="math math-inline">{tex}</span>')

        return MATH_RE.sub(repl, "\n".join(lines)).split("\n")


class BlogExtension(Extension):
    def extendMarkdown(self, md):
        # 35: before html_block (so callout <div>s are seen); 24: after fenced_code (25)
        md.preprocessors.register(CalloutPreprocessor(md), "callouts", 35)
        md.preprocessors.register(MathPreprocessor(md), "math", 24)


# ───────────────────────────── helpers ─────────────────────────────

LANG_LABELS = {
    "js": "JavaScript", "javascript": "JavaScript", "ts": "TypeScript", "typescript": "TypeScript",
    "py": "Python", "python": "Python", "bash": "Bash", "sh": "Shell", "shell": "Shell",
    "console": "Terminal", "sql": "SQL", "json": "JSON", "html": "HTML", "css": "CSS",
    "dart": "Dart", "java": "Java", "yaml": "YAML", "yml": "YAML", "http": "HTTP",
    "text": "Text", "txt": "Text", "xml": "XML", "diff": "Diff", "dockerfile": "Dockerfile",
    "toml": "TOML", "ini": "INI",
}

CODE_RE = re.compile(r'<pre><code(?: class="language-([\w+#.-]+)")?>(.*?)</code></pre>', re.S)
TABLE_RE = re.compile(r"<table>(.*?)</table>", re.S)
IMG_RE = re.compile(r"<img\s([^>]*?)\s*/?>")
ROOT_ATTR_RE = re.compile(r'(href|src)="/(?!/)')
TAG_RE = re.compile(r"<[^>]+>")


def slugify(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "x"


def fmt_date(d: dt.date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def iso(d: dt.date) -> str:
    return d.isoformat()


def plain_text(fragment: str) -> str:
    fragment = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S)
    fragment = re.sub(r'<a class="headerlink".*?</a>', "", fragment, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", fragment))).strip()


def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def image_size(path: Path):
    """Best-effort intrinsic size, so <img> can reserve space and avoid layout shift."""
    try:
        if path.suffix.lower() == ".svg":
            txt = path.read_text("utf-8", errors="ignore")[:2000]
            vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', txt)
            if vb:
                return int(float(vb.group(1))), int(float(vb.group(2)))
            return None
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def highlight_code(m: re.Match) -> str:
    lang = (m.group(1) or "text").lower()
    code = html.unescape(m.group(2)).rstrip("\n")
    try:
        lexer = get_lexer_by_name(lang)
    except ClassNotFound:
        lexer = TextLexer()
    body = pyg_highlight(code, lexer, HtmlFormatter(nowrap=True)).rstrip("\n")
    label = LANG_LABELS.get(lang, lang.capitalize())
    return (
        f'<div class="code-block" data-lang="{html.escape(lang)}">'
        f'<div class="code-block__bar"><span class="code-block__lang">{html.escape(label)}</span>'
        f'<button class="code-copy" type="button" aria-label="Copy {html.escape(label)} code to clipboard">'
        f'<span class="code-copy__label">Copy</span></button></div>'
        f'<pre tabindex="0"><code>{body}</code></pre></div>'
    )


def decorate_images(fragment: str) -> str:
    def repl(m):
        attrs = m.group(1)
        extra = []
        if "loading=" not in attrs:
            extra.append('loading="lazy"')
        if "decoding=" not in attrs:
            extra.append('decoding="async"')
        src = re.search(r'src="([^"]+)"', attrs)
        if src and "width=" not in attrs and src.group(1).startswith("/"):
            size = image_size(STATIC / src.group(1).lstrip("/"))
            if size:
                extra.append(f'width="{size[0]}" height="{size[1]}"')
        return f"<img {attrs} {' '.join(extra)}>".replace("  ", " ")

    return IMG_RE.sub(repl, fragment)


def render_markdown(text: str):
    md = markdown.Markdown(
        extensions=[
            BlogExtension(),
            "fenced_code", "tables", "attr_list", "md_in_html", "sane_lists",
            TocExtension(permalink="#", permalink_title="Link to this section", toc_depth="2-3"),
        ],
        output_format="html",
    )
    body = md.convert(text)
    toc = getattr(md, "toc_tokens", [])
    text_only = plain_text(body)
    has_math = 'class="math ' in body
    body = CODE_RE.sub(highlight_code, body)
    body = TABLE_RE.sub(
        r'<div class="table-wrap" role="region" aria-label="Scrollable table" tabindex="0"><table>\1</table></div>', body
    )
    body = decorate_images(body)
    body = ROOT_ATTR_RE.sub(rf'\1="{ROOT_TOKEN}', body)
    return body, toc, text_only, has_math


def split_front_matter(text: str, path: Path):
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not m:
        raise SystemExit(f"{path.name}: missing YAML front matter (--- … ---)")
    return (yaml.safe_load(m.group(1)) or {}), m.group(2)


def as_date(v, path: Path, field: str):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    if isinstance(v, str):
        try:
            return dt.date.fromisoformat(v.strip())
        except ValueError:
            pass
    raise SystemExit(f"{path.name}: `{field}` must be a date like 2026-05-14")


# ─────────────────────── generated artwork (SVG covers) ───────────────────────

TOPIC_COLORS = {
    "ai": "#b79cff",
    "cybersecurity": "#4ad6e8",
    "programming": "#5fd39a",
    "projects": "#f2b45a",
}
# Neutral light-UI tones used only by the project-screenshot mockup generator.
INK = "#12141c"
PAPER_1 = "#ffffff"
PAPER_2 = "#eef1f8"


def cover_svg(slug: str, topic: str) -> str:
    """Deterministic abstract cover art — no image files needed, tiny, and crisp at any size."""
    rnd = random.Random(int(hashlib.sha256(slug.encode()).hexdigest()[:12], 16))
    c = TOPIC_COLORS.get(topic, "#8aa4ff")
    gx, gy = rnd.uniform(0.55, 0.85), rnd.uniform(0.2, 0.6)
    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">',
        "<defs>",
        '<linearGradient id="b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0c0e15"/><stop offset="1" stop-color="#151a2b"/></linearGradient>',
        f'<radialGradient id="g" cx="{gx:.2f}" cy="{gy:.2f}" r=".75"><stop offset="0" stop-color="{c}" stop-opacity=".32"/><stop offset="1" stop-color="{c}" stop-opacity="0"/></radialGradient>',
        '<pattern id="p" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#fff" stroke-opacity=".045"/></pattern>',
        "</defs>",
        '<rect width="1200" height="630" fill="url(#b)"/>',
        '<rect width="1200" height="630" fill="url(#g)"/>',
        '<rect width="1200" height="630" fill="url(#p)"/>',
    ]
    if topic == "ai":
        layers = [rnd.randint(3, 5) for _ in range(rnd.randint(4, 5))]
        xs = [520 + i * (620 / (len(layers) - 1)) for i in range(len(layers))]
        pts = []
        for x, n in zip(xs, layers):
            top, bot = 110 + (6 - n) * 22, 520 - (6 - n) * 22
            pts.append([(x + rnd.uniform(-14, 14), top + j * (bot - top) / max(n - 1, 1)) for j in range(n)])
        edges, hot = [], []
        for a, b in zip(pts, pts[1:]):
            for p in a:
                for q in b:
                    edges.append(f"M{p[0]:.0f} {p[1]:.0f}L{q[0]:.0f} {q[1]:.0f}")
        for a, b in zip(pts, pts[1:]):
            p, q = rnd.choice(a), rnd.choice(b)
            hot.append(f"M{p[0]:.0f} {p[1]:.0f}L{q[0]:.0f} {q[1]:.0f}")
        out.append(f'<path d="{"".join(edges)}" stroke="{c}" stroke-opacity=".16" fill="none"/>')
        out.append(f'<path d="{"".join(hot)}" stroke="{c}" stroke-opacity=".75" stroke-width="2" fill="none"/>')
        for layer in pts:
            for x, y in layer:
                big = rnd.random() < 0.22
                out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{11 if big else 7}" fill="{c if big else "#0c0e15"}" stroke="{c}" stroke-opacity="{.9 if big else .55}" stroke-width="2"/>')
    elif topic == "cybersecurity":
        r = 40
        w, h = r * 2, 3 ** 0.5 * r
        for row in range(-1, 9):
            for col in range(-1, 12):
                cx = 470 + col * w * 0.75
                cy = 40 + row * h + (h / 2 if col % 2 else 0)
                pts = " ".join(f"{cx + r * math.cos(k * math.pi / 3):.0f},{cy + r * math.sin(k * math.pi / 3):.0f}" for k in range(6))
                fill = f'fill="{c}" fill-opacity=".16"' if rnd.random() < 0.1 else 'fill="none"'
                out.append(f'<polygon points="{pts}" {fill} stroke="{c}" stroke-opacity=".13"/>')
        out.append(
            f'<g transform="translate(860 315) scale(1.35)" fill="#0c0e15" stroke="{c}" stroke-width="3" stroke-linejoin="round">'
            '<path d="M0-110 90-70v80c0 60-45 95-90 115-45-20-90-55-90-115v-80z" fill-opacity=".85"/>'
            f'<circle cx="0" cy="-8" r="20" fill="none"/><path d="M0 12v38" stroke-linecap="round"/></g>'
        )
    elif topic == "programming":
        out.append('<rect x="540" y="96" width="560" height="438" rx="18" fill="#fff" fill-opacity=".035" stroke="#fff" stroke-opacity=".12"/>')
        out.append('<path d="M540 148H1100" stroke="#fff" stroke-opacity=".1"/>')
        for i in range(3):
            out.append(f'<circle cx="{574 + i * 24}" cy="122" r="6" fill="#fff" fill-opacity=".18"/>')
        y = 184
        indent = 0
        for _ in range(12):
            x = 576 + indent * 34
            for _seg in range(rnd.randint(1, 3)):
                wd = rnd.choice([48, 72, 96, 132, 168])
                col = rnd.choice([c, "#fff", "#8aa4ff", "#fff"])
                op = .75 if col == c else .28
                out.append(f'<rect x="{x}" y="{y}" width="{wd}" height="12" rx="6" fill="{col}" fill-opacity="{op}"/>')
                x += wd + 14
            y += 27
            indent = max(0, min(3, indent + rnd.choice([-1, 0, 0, 1])))
    else:  # projects
        out.append(f'<rect x="760" y="215" width="200" height="200" rx="20" fill="#0c0e15" stroke="{c}" stroke-opacity=".8" stroke-width="3"/>')
        out.append(f'<rect x="805" y="260" width="110" height="110" rx="10" fill="{c}" fill-opacity=".14" stroke="{c}" stroke-opacity=".5"/>')
        traces = []
        for k in range(14):
            side = rnd.choice("lrtb")
            off = 780 + rnd.randint(0, 8) * 20
            if side == "l":
                x, y = 760, 235 + (k % 9) * 20
                pts = [(x, y), (x - rnd.randint(40, 180), y), (x - rnd.randint(200, 320), y + rnd.choice([-1, 1]) * rnd.randint(30, 120))]
            elif side == "r":
                x, y = 960, 235 + (k % 9) * 20
                pts = [(x, y), (x + rnd.randint(40, 160), y), (x + rnd.randint(180, 240), y + rnd.choice([-1, 1]) * rnd.randint(30, 120))]
            elif side == "t":
                x, y = off, 215
                pts = [(x, y), (x, y - rnd.randint(30, 100)), (x + rnd.choice([-1, 1]) * rnd.randint(60, 240), y - rnd.randint(110, 190))]
            else:
                x, y = off, 415
                pts = [(x, y), (x, y + rnd.randint(30, 90)), (x + rnd.choice([-1, 1]) * rnd.randint(60, 240), y + rnd.randint(100, 170))]
            d = "M" + "L".join(f"{px:.0f} {py:.0f}" for px, py in pts)
            traces.append(d)
            ex, ey = pts[-1]
            out.append(f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="6" fill="#0c0e15" stroke="{c}" stroke-width="2" stroke-opacity=".8"/>')
        out.append(f'<path d="{"".join(traces)}" fill="none" stroke="{c}" stroke-opacity=".5" stroke-width="2" stroke-linejoin="round"/>')
    out.append("</svg>")
    return "".join(out)


def hero_network_svg() -> Markup:
    """A faint feed-forward network drawn as one path + circles (≈3 KB)."""
    rnd = random.Random(7)
    layers = [3, 5, 6, 5, 2]
    W, H = 640, 520
    pts = []
    for i, n in enumerate(layers):
        x = 30 + i * (W - 60) / (len(layers) - 1)
        pts.append([(x, 40 + (j + 0.5) * (H - 80) / n + rnd.uniform(-8, 8)) for j in range(n)])
    d = "".join(f"M{p[0]:.0f} {p[1]:.0f}L{q[0]:.0f} {q[1]:.0f}" for a, b in zip(pts, pts[1:]) for p in a for q in b)
    nodes = []
    k = 0
    for layer in pts:
        for x, y in layer:
            pulse = ' class="pulse" style="--d:%.1fs"' % rnd.uniform(0, 5) if rnd.random() < 0.22 else ""
            nodes.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{4 if pulse else 3}"{pulse}/>')
            k += 1
    return Markup(
        f'<svg class="hero-net" viewBox="0 0 {W} {H}" aria-hidden="true" focusable="false">'
        f'<path d="{d}" fill="none" stroke="currentColor" stroke-opacity=".16"/>'
        f'<g fill="currentColor">{"".join(nodes)}</g></svg>'
    )


MOCKUP_KINDS = ["list", "detail", "dashboard"]


def app_mockup_svg(slug: str, index: int, color: str) -> str:
    """A placeholder phone-screen mockup for a project with no real screenshots
    yet — same paper/ink/halftone language as the article cover art, just in a
    portrait phone frame, so a project page never looks unfinished before you
    swap in real images."""
    rnd = random.Random(int(hashlib.sha256(f"{slug}-{index}".encode()).hexdigest()[:12], 16))
    kind = MOCKUP_KINDS[index % len(MOCKUP_KINDS)]
    W, H = 360, 760
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
        "<defs>",
        f'<linearGradient id="b" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PAPER_1}"/><stop offset="1" stop-color="{PAPER_2}"/></linearGradient>',
        f'<pattern id="p" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="1.2" cy="1.2" r="1.2" fill="{INK}" fill-opacity=".06"/></pattern>',
        f'<clipPath id="scr"><rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="34"/></clipPath>',
        "</defs>",
        f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="42" fill="#17130e"/>',
        f'<g clip-path="url(#scr)">',
        f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" fill="url(#b)"/>',
        f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" fill="url(#p)"/>',
        f'<rect x="14" y="14" width="{W - 28}" height="64" fill="{color}" fill-opacity=".9"/>',
        f'<circle cx="44" cy="46" r="10" fill="{PAPER_1}" fill-opacity=".9"/>',
        f'<rect x="68" y="38" width="{rnd.randint(80, 130)}" height="14" rx="4" fill="{PAPER_1}" fill-opacity=".85"/>',
    ]
    y = 104
    if kind == "list":
        for _ in range(rnd.randint(5, 7)):
            h = rnd.choice([64, 72, 80])
            out.append(f'<rect x="26" y="{y}" width="{W - 52}" height="{h}" rx="12" fill="{INK}" fill-opacity=".035" stroke="{INK}" stroke-opacity=".14"/>')
            out.append(f'<circle cx="{50}" cy="{y + h / 2:.0f}" r="14" fill="{color}" fill-opacity="{0.8 if rnd.random() < 0.3 else 0.18}"/>')
            out.append(f'<rect x="78" y="{y + h / 2 - 12:.0f}" width="{rnd.randint(90, 160)}" height="10" rx="3" fill="{INK}" fill-opacity=".55"/>')
            out.append(f'<rect x="78" y="{y + h / 2 + 4:.0f}" width="{rnd.randint(60, 110)}" height="8" rx="3" fill="{INK}" fill-opacity=".25"/>')
            y += h + 14
    elif kind == "detail":
        out.append(f'<rect x="26" y="{y}" width="{W - 52}" height="160" rx="16" fill="{INK}" fill-opacity=".04" stroke="{INK}" stroke-opacity=".14"/>')
        y += 182
        for _ in range(4):
            wd = rnd.choice([70, 90, 120, 150])
            out.append(f'<rect x="26" y="{y}" width="{wd}" height="11" rx="3" fill="{INK}" fill-opacity="{0.5 if wd > 100 else 0.22}"/>')
            y += 24
        y += 20
        out.append(f'<rect x="26" y="{y}" width="{W - 52}" height="48" rx="24" fill="{color}" fill-opacity=".85"/>')
        out.append(f'<rect x="{W / 2 - 40:.0f}" y="{y + 18:.0f}" width="80" height="12" rx="4" fill="{PAPER_1}"/>')
        y += 80
    else:  # dashboard
        card_w = (W - 52 - 14) / 2
        for i in range(4):
            cx = 26 + (i % 2) * (card_w + 14)
            cy = y + (i // 2) * 110
            out.append(f'<rect x="{cx:.0f}" y="{cy}" width="{card_w:.0f}" height="96" rx="14" fill="{INK}" fill-opacity=".035" stroke="{INK}" stroke-opacity=".14"/>')
            out.append(f'<rect x="{cx + 14:.0f}" y="{cy + 16}" width="{card_w - 28:.0f}" height="10" rx="3" fill="{INK}" fill-opacity=".3"/>')
            out.append(f'<rect x="{cx + 14:.0f}" y="{cy + 38}" width="{rnd.randint(30, 50)}" height="22" rx="4" fill="{color}" fill-opacity=".8"/>')
        y += 240
        out.append(f'<rect x="26" y="{y}" width="{W - 52}" height="120" rx="14" fill="{INK}" fill-opacity=".03" stroke="{INK}" stroke-opacity=".14"/>')
        pts = " ".join(f"{26 + i * (W - 52) / 7:.0f},{y + 90 - rnd.randint(10, 85)}" for i in range(8))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.5" stroke-linejoin="round"/>')
    out.append(f'<rect x="14" y="{H - 66}" width="{W - 28}" height="52" fill="{PAPER_1}" fill-opacity=".92" stroke="{INK}" stroke-opacity=".1"/>')
    for i in range(4):
        cx = 14 + (W - 28) * (i + 0.5) / 4
        out.append(f'<circle cx="{cx:.0f}" cy="{H - 40}" r="9" fill="{color if i == 0 else INK}" fill-opacity="{0.8 if i == 0 else 0.22}"/>')
    out.append("</g>")
    out.append(f'<rect x="2" y="2" width="{W - 4}" height="{H - 4}" rx="42" fill="none" stroke="{INK}" stroke-opacity=".5" stroke-width="2.5"/>')
    out.append(f'<rect x="{W / 2 - 34:.0f}" y="10" width="68" height="20" rx="10" fill="#17130e"/>')
    out.append("</svg>")
    return "".join(out)


def find_font(names, size):
    from PIL import ImageFont

    dirs = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation",
            "/Library/Fonts", "/System/Library/Fonts/Supplemental", "C:/Windows/Fonts"]
    for n in names:
        for d in dirs:
            p = Path(d) / n
            if p.exists():
                return ImageFont.truetype(str(p), size)
    return ImageFont.load_default(size)


def make_og_png(out: Path, title: str, kicker: str, accent: str, brand: str, host: str):
    """1200×630 social card. Optional: skipped silently if Pillow is missing."""
    try:
        from PIL import Image, ImageDraw, ImageOps
    except ImportError:
        return False
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (9, 10, 14))

    def glow(cx, cy, r, color, k):
        g = ImageOps.invert(Image.radial_gradient("L")).resize((2 * r, 2 * r)).point(lambda v: int(v * k))
        img.paste(Image.new("RGB", (2 * r, 2 * r), color), (cx - r, cy - r), g)

    glow(1040, 70, 560, hex_to_rgb(accent), 0.34)
    glow(60, 640, 460, (138, 164, 255), 0.2)
    d = ImageDraw.Draw(img, "RGBA")
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(255, 255, 255, 9))
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(255, 255, 255, 9))
    bold = ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"]
    reg = ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "Arial.ttf", "arial.ttf"]
    kf = find_font(reg, 30)
    kw = d.textlength(kicker, font=kf)
    d.rounded_rectangle([80, 78, 80 + kw + 40, 78 + 52], radius=10, fill=(*hex_to_rgb(accent), 40), outline=(*hex_to_rgb(accent), 120))
    d.text((100, 87), kicker, font=kf, fill=hex_to_rgb(accent))
    size = 68
    while True:
        tf = find_font(bold, size)
        lines, cur = [], ""
        for w in title.split():
            t = f"{cur} {w}".strip()
            if d.textlength(t, font=tf) <= 1040:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if len(lines) <= 3 or size <= 44:
            break
        size -= 6
    y = 175
    for ln in lines[:4]:
        d.text((80, y), ln, font=tf, fill=(236, 239, 246))
        y += int(size * 1.22)
    d.line([(80, 540), (1120, 540)], fill=(255, 255, 255, 30))
    d.text((80, 560), brand, font=find_font(bold, 30), fill=(236, 239, 246))
    hw = d.textlength(host, font=kf)
    d.text((1120 - hw, 562), host, font=kf, fill=(163, 170, 186))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    return True


def minify_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    return css.replace(";}", "}").strip()


# ───────────────────────────── build ─────────────────────────────

def load_config(site_url: str | None):
    cfg = yaml.safe_load((BASE / "site.yml").read_text("utf-8"))
    if site_url:
        cfg["url"] = site_url
    cfg["url"] = cfg["url"].rstrip("/")
    cfg["base_path"] = urlparse(cfg["url"]).path.rstrip("/")
    cfg["host"] = urlparse(cfg["url"]).netloc
    return cfg


def load_posts(cfg, topics, cat_to_topic):
    posts = []
    seen = set()
    for path in sorted((CONTENT / "posts").glob("*.md")):
        fm, body = split_front_matter(path.read_text("utf-8"), path)
        if fm.get("draft"):
            continue
        stem = path.stem
        dm = re.match(r"^(\d{4}-\d{2}-\d{2})-(.+)$", stem)
        slug = fm.get("slug") or (dm.group(2) if dm else stem)
        if slug in seen:
            raise SystemExit(f"Duplicate slug: {slug}")
        seen.add(slug)
        for req in ("title", "description", "category"):
            if not fm.get(req):
                raise SystemExit(f"{path.name}: front matter is missing `{req}`")
        date = as_date(fm.get("date") or (dm.group(1) if dm else None), path, "date")
        updated = as_date(fm["updated"], path, "updated") if fm.get("updated") else None
        category = fm["category"]
        topic_slug = fm.get("topic") or cat_to_topic.get(category)
        if not topic_slug:
            raise SystemExit(
                f"{path.name}: category '{category}' is not assigned to a topic. "
                f"Add it to `topics` in site.yml (known: {', '.join(cat_to_topic)})"
            )
        html_body, toc, text, has_math = render_markdown(body)
        words = len(text.split())
        tags = []
        for t in fm.get("tags", []):
            t = str(t).lstrip("#")
            tags.append(SimpleNamespace(name=t, slug=slugify(t)))
        p = SimpleNamespace(
            slug=slug, url=f"posts/{slug}/", title=fm["title"], description=fm["description"],
            date=date, updated=updated, category=category, topic=topic_slug,
            type=fm.get("type", "article"), tags=tags, featured=bool(fm.get("featured")),
            author=fm.get("author") or cfg["author"]["name"],
            html=html_body, toc=toc, text=text, has_math=has_math,
            reading_time=max(1, round(words / WORDS_PER_MINUTE)), words=words,
            image=fm.get("image"), image_alt=fm.get("image_alt"),
        )
        p.category_slug = slugify(category)
        p.cover = p.image or f"assets/covers/{slug}.svg"
        p.cover_is_generated = not p.image
        p.og = p.image if p.image else f"assets/og/{slug}.png"
        posts.append(p)
    posts.sort(key=lambda p: (p.date, p.slug), reverse=True)
    return posts


def related_posts(post, posts, n=3):
    scored = []
    tagset = {t.slug for t in post.tags}
    for o in posts:
        if o is post:
            continue
        s = 3 * (o.category == post.category) + 2 * len(tagset & {t.slug for t in o.tags}) + (o.topic == post.topic)
        scored.append((s, o.date, o))
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [o for s, _, o in scored[:n]]


def related_projects(project, projects, n=3):
    scored = []
    own_filters = set(project["filters"])
    for o in projects:
        if o is project:
            continue
        scored.append((len(own_filters & set(o["filters"])), o))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [o for s, o in scored[:n] if s > 0] or [o for o in projects if o is not project][:n]


def write(out_dir: Path, rel: str, data: str | bytes):
    p = out_dir / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        p.write_text(data, "utf-8")
    else:
        p.write_bytes(data)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site-url", help="Public site URL (overrides site.yml)")
    ap.add_argument("--out", default="dist", help="Output directory (default: dist)")
    ap.add_argument("--serve", action="store_true", help="Serve the built site locally after building")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-minify", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.site_url)
    out = (BASE / args.out).resolve()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(STATIC, out)
    write(out, ".nojekyll", "")

    # assets: minify CSS + content-hash for cache busting
    css_path = out / "assets/css/main.css"
    css = css_path.read_text("utf-8")
    if not args.no_minify:
        css = minify_css(css)
        css_path.write_text(css, "utf-8")
    versions = {
        "css": hashlib.md5(css.encode()).hexdigest()[:8],
        "js": hashlib.md5((out / "assets/js/main.js").read_bytes()).hexdigest()[:8],
    }

    # data
    topics = cfg["topics"]
    topic_by_slug = {t["slug"]: t for t in topics}
    cat_to_topic = {c: t["slug"] for t in topics for c in t["categories"]}
    posts = load_posts(cfg, topics, cat_to_topic)
    projects = yaml.safe_load((CONTENT / "projects.yml").read_text("utf-8")) or []
    project_colors = list(TOPIC_COLORS.values())
    for pr in projects:
        pr["slug"] = slugify(pr["name"])
        pr["tagline"] = pr.get("tagline") or pr["description"]
        pr["highlights"] = pr.get("highlights") or []
        pr["color"] = project_colors[int(hashlib.sha256(pr["slug"].encode()).hexdigest()[:8], 16) % len(project_colors)]

        shots = pr.get("screenshots") or []
        pr["screenshots"] = [
            {"src": s, "alt": f"{pr['name']} screenshot {i + 1}"} if isinstance(s, str)
            else {"src": s["src"], "alt": s.get("alt") or f"{pr['name']} screenshot {i + 1}"}
            for i, s in enumerate(shots)
        ]

        body_path = CONTENT / "projects" / f"{pr['slug']}.md"
        if body_path.exists():
            html_body, toc, _text, has_math = render_markdown(body_path.read_text("utf-8"))
            pr["body_html"], pr["toc"], pr["has_math"] = html_body, toc, has_math
        else:
            pr["body_html"], pr["toc"], pr["has_math"] = None, [], False
    about = yaml.safe_load((CONTENT / "about.yml").read_text("utf-8"))

    tags = {}
    for p in posts:
        for t in p.tags:
            tags.setdefault(t.slug, SimpleNamespace(name=t.name, slug=t.slug, posts=[]))
            tags[t.slug].posts.append(p)
    tag_list = sorted(tags.values(), key=lambda t: (-len(t.posts), t.name.lower()))

    for t in topics:
        t["posts"] = [p for p in posts if p.topic == t["slug"]]
        t["count"] = len(t["posts"])
        t["category_counts"] = [
            {"name": c, "slug": slugify(c), "count": sum(1 for p in t["posts"] if p.category == c)}
            for c in t["categories"]
        ]

    # generated artwork
    for p in posts:
        if p.cover_is_generated:
            write(out, p.cover, cover_svg(p.slug, p.topic))
        if not p.image:
            make_og_png(out / p.og, p.title, p.category, TOPIC_COLORS.get(p.topic, "#8aa4ff"), cfg["name"], cfg["host"])
    if not make_og_png(out / cfg["og_image"], cfg["tagline"], "Personal engineering blog", "#8aa4ff", cfg["name"], cfg["host"]):
        print("  (Pillow not installed — using the OG image from static/ if present)")

    # templates
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True, lstrip_blocks=True,
    )
    env.filters.update(fmt_date=fmt_date, iso=iso)
    env.globals.update(
        site=cfg, icon=icon, hero_network=hero_network_svg, topic_by_slug=topic_by_slug,
        topics=topics, versions=versions, now=dt.date.today(),
        nav=[
            ("home", "Home", ""), ("ai", "AI", "topics/ai/"),
            ("cybersecurity", "Cybersecurity", "topics/cybersecurity/"),
            ("tutorials", "Tutorials", "tutorials/"),
            ("projects", "Projects", "projects/"),
            ("about", "About", "about/"),
        ],
    )

    abs_url = lambda rel: f"{cfg['url']}/{rel}"
    site_ld = {"@type": "Person", "name": cfg["author"]["name"], "url": abs_url(""),
               "sameAs": [u for u in (cfg["author"].get("github"), cfg["author"].get("linkedin")) if u]}

    def breadcrumb_ld(items):
        return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": abs_url(u)} for i, (n, u) in enumerate(items)]}

    pages_for_sitemap = []

    def render(tpl, rel, root_override=None, sitemap=True, lastmod=None, **ctx):
        depth = rel.count("/")
        root = root_override or ("../" * depth or "./")
        url_path = rel[: -len("index.html")] if rel.endswith("index.html") else rel
        ctx.setdefault("nav_active", "")
        ctx.setdefault("jsonld", [])
        ctx.setdefault("og_type", "website")
        ctx.setdefault("og_image", cfg["og_image"])
        ctx.setdefault("page_title", cfg["title"])
        ctx.setdefault("page_description", cfg["description"])
        page = env.get_template(tpl).render(root=root, page_url=url_path, canonical=abs_url(url_path), **ctx)
        write(out, rel, page.replace(ROOT_TOKEN, root))
        if sitemap:
            pages_for_sitemap.append((abs_url(url_path), lastmod))

    # ── home
    featured = [p for p in posts if p.featured][:3]
    if len(featured) < 3 and len(posts) > 3:
        featured += [p for p in posts if p not in featured][: 3 - len(featured)]
    latest = [p for p in posts if p not in featured][:6]
    feat_project = next((x for x in projects if x.get("featured")), projects[0] if projects else None)
    render(
        "home.html", "index.html", posts=posts, featured=featured, latest=latest, projects=projects,
        feat_project=feat_project, about=about, newest=posts[0] if posts else None,
        nav_active="home",
        jsonld=[{"@context": "https://schema.org", "@type": "WebSite", "name": cfg["name"], "url": abs_url(""),
                 "description": cfg["description"], "inLanguage": cfg["language"], "author": site_ld}],
    )

    # ── listings
    def listing(rel, **kw):
        crumbs = [("Home", "")] + kw.pop("crumbs")
        render("listing.html", rel, jsonld=[breadcrumb_ld(crumbs)], crumbs=crumbs, **kw)

    all_cats = []
    for t in topics:
        all_cats += [c for c in t["category_counts"] if c["count"]]
    listing("articles/index.html", crumbs=[("Articles", "articles/")], heading="All articles",
            page_title=f"All articles | {cfg['name']}",
            page_description="Every article on AI, machine learning, cybersecurity and programming, newest first.",
            intro="Every article on the site, newest first. Filter by category to narrow things down.",
            posts=posts, filters=all_cats, nav_active="")
    for t in topics:
        listing(f"topics/{t['slug']}/index.html", crumbs=[("Topics", "articles/"), (t["name"], f"topics/{t['slug']}/")],
                heading=t["name"], topic=t, page_title=f"{t['name']} articles | {cfg['name']}",
                page_description=t["description"], intro=t["description"], posts=t["posts"],
                filters=[c for c in t["category_counts"] if c["count"]],
                nav_active=t["slug"] if t["slug"] in ("ai", "cybersecurity") else "")

    tut = [p for p in posts if p.type == "tutorial"]
    listing("tutorials/index.html", crumbs=[("Tutorials", "tutorials/")], heading="Tutorials",
            page_title=f"Tutorials | {cfg['name']}",
            page_description="Step-by-step, reproducible tutorials on AI, security and programming.",
            intro="Step-by-step guides you can follow on a laptop. Each one lists prerequisites and ends with something that runs.",
            posts=tut, filters=[{"name": c, "slug": slugify(c), "count": sum(1 for p in tut if p.category == c)}
                                for c in dict.fromkeys(p.category for p in tut)], nav_active="tutorials")

    render("tags.html", "tags/index.html", tags=tag_list, posts_total=len(posts), page_title=f"Tags | {cfg['name']}",
           page_description="Browse every topic tag used on the blog.",
           jsonld=[breadcrumb_ld([("Home", ""), ("Tags", "tags/")])])
    for t in tag_list:
        listing(f"tags/{t.slug}/index.html", crumbs=[("Tags", "tags/"), (f"#{t.name}", f"tags/{t.slug}/")],
                heading=f"#{t.name}", page_title=f"#{t.name} articles | {cfg['name']}",
                page_description=f"Articles tagged {t.name}.", intro=f"{len(t.posts)} article{'s' if len(t.posts) != 1 else ''} tagged {t.name}.",
                posts=t.posts, filters=[], is_tag=True)

    # ── projects / about / 404
    pf = [("ai", "AI"), ("cybersecurity", "Cybersecurity"), ("flutter", "Flutter"), ("backend", "Backend"), ("web", "Web")]
    project_filters = [f for f in [{"slug": s, "name": n, "count": sum(1 for x in projects if s in x["filters"])} for s, n in pf] if f["count"] > 0]
    render("projects.html", "projects/index.html", projects=projects, project_filters=project_filters, nav_active="projects",
           page_title=f"Projects | {cfg['name']}",
           page_description="Open-source projects, experiments and security labs.",
           jsonld=[breadcrumb_ld([("Home", ""), ("Projects", "projects/")])])
    for pr in projects:
        crumbs = [("Home", ""), ("Projects", "projects/"), (pr["name"], f"projects/{pr['slug']}/")]
        ld = {
            "@context": "https://schema.org", "@type": "SoftwareSourceCode", "name": pr["name"],
            "description": pr["description"], "codeRepository": pr.get("github", ""),
            "programmingLanguage": pr["tech"], "author": {"@type": "Person", "name": cfg["author"]["name"]},
        }
        render("project.html", f"projects/{pr['slug']}/index.html", project=pr, crumbs=crumbs,
               related=related_projects(pr, projects), nav_active="projects",
               page_title=f"{pr['name']} | {cfg['name']}", page_description=pr["description"],
               og_type="website", jsonld=[ld, breadcrumb_ld(crumbs)])
    render("about.html", "about/index.html", about=about, nav_active="about", projects=projects,
           page_title=f"About | {cfg['name']}", page_description=cfg["author"]["bio"],
           jsonld=[{"@context": "https://schema.org", "@type": "ProfilePage", "mainEntity": {**site_ld, "jobTitle": cfg["author"]["role"]}},
                   breadcrumb_ld([("Home", ""), ("About", "about/")])])
    render("404.html", "404.html", root_override=(cfg["base_path"] or "") + "/", sitemap=False,
           page_title=f"Page not found | {cfg['name']}", page_description="This page doesn't exist.")

    # ── articles
    by_date = sorted(posts, key=lambda p: (p.date, p.slug))
    for i, p in enumerate(posts):
        idx = by_date.index(p)
        prev_p = by_date[idx - 1] if idx > 0 else None
        next_p = by_date[idx + 1] if idx < len(by_date) - 1 else None
        topic = topic_by_slug[p.topic]
        crumbs = [("Home", ""), (topic["name"], f"topics/{topic['slug']}/"), (p.title, p.url)]
        ld = {
            "@context": "https://schema.org", "@type": "BlogPosting", "headline": p.title,
            "description": p.description, "datePublished": iso(p.date), "dateModified": iso(p.updated or p.date),
            "author": {"@type": "Person", "name": p.author, "url": abs_url("about/")},
            "publisher": {"@type": "Person", "name": cfg["author"]["name"]},
            "image": abs_url(p.og) if not p.og.startswith("http") else p.og,
            "mainEntityOfPage": abs_url(p.url), "keywords": ", ".join(t.name for t in p.tags),
            "articleSection": p.category, "wordCount": p.words, "inLanguage": cfg["language"],
        }
        render("post.html", f"{p.url}index.html", post=p, topic=topic, related=related_posts(p, posts),
               prev_post=prev_p, next_post=next_p, crumbs=crumbs, nav_active="",
               page_title=f"{p.title} | {cfg['name']}", page_description=p.description,
               og_type="article", og_image=p.og, jsonld=[ld, breadcrumb_ld(crumbs)], lastmod=iso(p.updated or p.date))

    # ── machine-readable files
    search = [{"t": p.title, "d": p.description, "c": p.category, "g": [t.name for t in p.tags], "u": p.url,
               "dt": fmt_date(p.date), "r": p.reading_time, "x": p.text[:9000]} for p in posts]
    write(out, "search.json", json.dumps(search, ensure_ascii=False, separators=(",", ":")))

    def feed_item(p):
        content = p.html.replace(ROOT_TOKEN, cfg["url"] + "/").replace("]]>", "]]&gt;")
        cat_names = list(dict.fromkeys([p.category] + [t.name for t in p.tags]))
        cats = "".join(f"<category>{xml_escape(c)}</category>" for c in cat_names)
        pub = format_datetime(dt.datetime.combine(p.date, dt.time(9, 0), tzinfo=dt.timezone.utc))
        return (f"<item><title>{xml_escape(p.title)}</title><link>{abs_url(p.url)}</link>"
                f'<guid isPermaLink="true">{abs_url(p.url)}</guid><pubDate>{pub}</pubDate>'
                f"<description>{xml_escape(p.description)}</description>{cats}"
                f"<content:encoded><![CDATA[{content}]]></content:encoded></item>")

    feed = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">'
            f"<channel><title>{xml_escape(cfg['name'])}</title><link>{abs_url('')}</link>"
            f"<description>{xml_escape(cfg['description'])}</description><language>{cfg['language']}</language>"
            f'<atom:link href="{abs_url("feed.xml")}" rel="self" type="application/rss+xml"/>'
            + "".join(feed_item(p) for p in posts[:20]) + "</channel></rss>")
    write(out, "feed.xml", feed)

    urls = "".join(
        f"<url><loc>{xml_escape(u)}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + "</url>"
        for u, lm in pages_for_sitemap)
    write(out, "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    write(out, "robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {abs_url('sitemap.xml')}\n")

    total = sum(1 for _ in out.rglob("*") if _.is_file())
    print(f"✓ Built {len(posts)} articles, {len(tag_list)} tags, {len(projects)} projects → {out.relative_to(BASE)}/ ({total} files)")
    print(f"  site url: {cfg['url']}")

    if args.serve:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(out))
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", args.port), handler) as httpd:
            print(f"  preview:  http://localhost:{args.port}/   (Ctrl+C to stop)")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print()


if __name__ == "__main__":
    sys.exit(main())
