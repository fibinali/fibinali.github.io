<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:atom="http://www.w3.org/2005/Atom">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title><xsl:value-of select="/rss/channel/title"/> · RSS Feed</title>
        <style>
          :root {
            --bg: #0e1222;
            --surface: #151a30;
            --border: #222949;
            --text: #e2e8f0;
            --muted: #94a3b8;
            --accent: #8aa4ff;
            --accent-grad: linear-gradient(135deg, #8aa4ff, #b79cff);
          }
          @media (prefers-color-scheme: light) {
            :root {
              --bg: #fafbfd;
              --surface: #ffffff;
              --border: #e2e8f0;
              --text: #0f172a;
              --muted: #64748b;
              --accent: #3b82f6;
              --accent-grad: linear-gradient(135deg, #3b82f6, #6366f1);
            }
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 2.5rem 1rem;
          }
          .container {
            max-width: 760px;
            margin: 0 auto;
          }
          .notice {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
          }
          .notice h1 {
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            background: var(--accent-grad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
          }
          .notice p {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 1rem;
          }
          .copy-box {
            display: flex;
            gap: 0.5rem;
            background: var(--bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 0.5rem 0.75rem;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.85rem;
            color: var(--accent);
            word-break: break-all;
          }
          .btn-home {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            font-size: 0.9rem;
            transition: all 0.2s ease;
          }
          .btn-home:hover {
            border-color: var(--accent);
            color: var(--accent);
          }
          .items {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
          }
          .item {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem;
            transition: transform 0.15s ease, border-color 0.15s ease;
          }
          .item:hover {
            border-color: var(--accent);
            transform: translateY(-2px);
          }
          .item h2 {
            font-size: 1.25rem;
            margin-bottom: 0.4rem;
          }
          .item h2 a {
            color: var(--text);
            text-decoration: none;
          }
          .item h2 a:hover {
            color: var(--accent);
          }
          .item-meta {
            font-size: 0.85rem;
            color: var(--muted);
            margin-bottom: 0.75rem;
          }
          .item-desc {
            color: var(--muted);
            font-size: 0.95rem;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="notice">
            <h1><xsl:value-of select="/rss/channel/title"/> — RSS Feed</h1>
            <p>
              This is an RSS feed. Subscribe by copying the URL below into your favorite news or feed reader (such as Feedly, Inoreader, or NetNewsWire).
            </p>
            <div class="copy-box">
              <xsl:value-of select="/rss/channel/atom:link/@href"/>
            </div>
            <a class="btn-home" href="{/rss/channel/link}">← Back to Website</a>
          </div>

          <h2 style="font-size: 1.1rem; color: var(--muted); margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 0.05em;">Recent Articles</h2>
          <ul class="items">
            <xsl:for-each select="/rss/channel/item">
              <li class="item">
                <h2>
                  <a href="{link}">
                    <xsl:value-of select="title"/>
                  </a>
                </h2>
                <div class="item-meta">
                  <xsl:value-of select="pubDate"/>
                </div>
                <p class="item-desc">
                  <xsl:value-of select="description"/>
                </p>
              </li>
            </xsl:for-each>
          </ul>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
