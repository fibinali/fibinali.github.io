# Alex Rivera — AI, Cybersecurity & Engineering Blog

A fast, static personal blog built for GitHub Pages: Markdown in, hand-tuned HTML out.
No Node, no bundler, no client-side framework — a ~800-line Python generator turns
`content/*.md` into a complete static site in about a second.

```
python build.py --serve
```

then open **http://localhost:8000**.

---

## 0. Design system

The site uses a modern developer look: a blue/purple accent pair, glass-panel
cards with soft glow shadows, and system fonts throughout (no font downloads).
It ships with two full palettes — light (white background, blue accent) and
dark (near-black, the same blue/purple lifted for contrast) — toggled by the
person reading, with light as the default. Both live as CSS custom properties
at the top of `static/assets/css/main.css`: `:root` holds the dark palette and
`[data-theme="light"]` overrides it for light mode. Change the hex values there
(and the four `TOPIC_COLORS` in `build.py`, which also drive the generated
cover art and project-screenshot placeholders) to retheme the whole site.

## 1. Make it yours first

Everything identity-related lives in **`site.yml`**: your name, bio, GitHub/LinkedIn
links, the site tagline, and the four topic definitions. Open it and replace every
`USERNAME` / placeholder value before you do anything else.

Then:

| File | Controls |
|---|---|
| `site.yml` | Name, bio, links, tagline, topics & their categories |
| `content/about.yml` | Everything on the About page (intro, journeys, tech stack) |
| `content/projects.yml` | Cards on the Projects page and the homepage feature slot |
| `content/posts/*.md` | Your articles |

Delete the seven example posts in `content/posts/` once you've got real content —
they exist so the site looks complete immediately after your first deploy, per the
original brief.

## 2. Project pages and screenshots

Every entry in `content/projects.yml` gets a card on `/projects/` **and** its
own detail page at `/projects/<slug>/` (the slug is the name, lowercased and
hyphenated) with a header, a "View on GitHub" / "Live demo" button pair, an
optional highlights list, and a screenshot gallery.

**To add your own screenshots** (a Flutter app, a CLI, a dashboard — anything):

1. Drop the image files anywhere under `static/assets/img/` — for example
   `static/assets/img/projects/securenotes/home.png`.
2. Reference them in that project's entry in `content/projects.yml`:
   ```yaml
   screenshots:
     - src: "assets/img/projects/securenotes/home.png"
       alt: "Home screen showing the encrypted notes list"
     - src: "assets/img/projects/securenotes/unlock.png"
       alt: "Biometric unlock prompt"
   ```
3. Rebuild. The gallery shows each image as a clickable thumbnail that opens
   full-size in a lightbox.

Leave `screenshots` out entirely and the build generates placeholder app-mockup
graphics automatically, so a project page never looks unfinished before you've
got real screenshots — swap them out whenever you're ready, no template
changes needed.

For a longer write-up than fits in the card description — an architecture
note, a "what I'd do differently" section, benchmark tables — add a Markdown
file at `content/projects/<slug>.md`. No front matter needed, just Markdown;
it supports the same callouts, syntax-highlighted code and table of contents
as blog posts, and renders automatically below the gallery if present.

## 3. Writing a post

Add a Markdown file to `content/posts/`. The filename can be anything; if it starts
with `YYYY-MM-DD-`, that date is used automatically and the rest of the filename
becomes the URL slug (`2026-09-22-my-post.md` → `/posts/my-post/`). Otherwise set
`date` and `slug` explicitly in the front matter.

```markdown
---
title: "Your Article Title"
description: "One or two sentences — used in cards, search and social previews."
category: "Machine Learning"        # must belong to a topic in site.yml
tags: [AI, Python]                  # optional
type: article                       # "article" or "tutorial"
featured: true                      # optional — eligible for the homepage feature slot
image: "https://…"                  # optional — omit to get generated cover art
---

Your Markdown content starts here.
```

**Callout blocks** — for security notes, warnings, examples, etc:

```markdown
::: security-note
Only test systems you own or have explicit permission to test.
:::
```

Available kinds: `note`, `important`, `warning`, `security-note`, `example`,
`command`, `vulnerability`, `mitigation`, `tip`. An optional custom title can follow
the kind on the same line (`::: warning Rate limits apply`).

**Math** — `$inline$` and `$$block$$`, rendered client-side with KaTeX (only loaded
on pages that actually contain a formula, so it costs nothing elsewhere).

**Code** — standard fenced code blocks with a language tag get syntax highlighting
and a copy button automatically: `python`, `javascript`, `dart`, `java`, `bash`,
`sql`, `html`, `css`, `json`, and more.

Run `python build.py --serve` again and your new post appears everywhere: the
homepage, its topic page, `/articles/`, `/tags/…`, `search.json` and `feed.xml`.

## 4. Cover images

If a post has no `image` set, the generator draws a unique, deterministic abstract
SVG cover for it (a different motif per topic — a small neural net for AI, a hex
grid with a shield for Cybersecurity, a code-window silhouette for Programming, a
circuit board for Projects) and a matching 1200×630 PNG for social sharing. Set
`image: "/assets/img/whatever.jpg"` in the front matter to use your own instead.

## 5. Deploying

A GitHub Actions workflow (`.github/workflows/deploy.yml`) is already set up to
build and publish on every push to `main`:

1. Push this repository to GitHub.
2. Repo **Settings → Pages → Source → GitHub Actions**.
3. Push to `main`. The workflow installs `requirements.txt`, runs
   `python build.py --site-url <your Pages URL>` (the URL is detected automatically,
   whether you're on `USERNAME.github.io` or a project site with a `/repo-name/`
   path), and publishes `dist/`.

No manual `--site-url` flag is needed for CI — `actions/configure-pages` supplies
the real URL. For local builds, `site.yml`'s `url` is used unless you pass
`--site-url` yourself.

### Custom domain

Add a `CNAME` file to `static/` with your domain in it (it'll be copied into every
build automatically), configure the DNS records GitHub documents, and set the custom
domain in **Settings → Pages**.

## 6. How the generator works, briefly

- `build.py` reads `site.yml` + `content/`, renders Markdown (with the callout and
  math preprocessors, Pygments syntax highlighting, and a table-of-contents
  extension), and passes everything to the Jinja2 templates in `templates/`.
- Every link in the output is relative, so the exact same `dist/` folder works at
  `https://USER.github.io/`, at `https://USER.github.io/repo-name/`, on a custom
  domain, or opened straight from disk. The one exception is `404.html`, which
  GitHub Pages serves for *any* unmatched path at *any* depth, so it deliberately
  uses a site-root-relative path instead.
- Search is a single `search.json` file fetched once by `assets/js/main.js` and
  matched client-side — no server, no third-party service.
- `robots.txt`, `sitemap.xml`, `feed.xml` and per-article JSON-LD are generated
  automatically from the same post data.

## 7. Local commands

```bash
python build.py                    # build into ./dist
python build.py --serve            # build, then preview at localhost:8000
python build.py --serve --port 3000
python build.py --site-url https://example.com   # override the URL for one build
python build.py --no-minify        # keep main.css readable, for debugging
```

Requires Python 3.10+ and the packages in `requirements.txt`
(`pip install -r requirements.txt`).
