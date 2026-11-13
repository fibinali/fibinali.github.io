<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:s="http://www.sitemaps.org/schemas/sitemap/0.9">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="en">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>Sitemap · XML URL List</title>
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
            max-width: 900px;
            margin: 0 auto;
          }
          .header {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
          }
          .header h1 {
            font-size: 1.6rem;
            margin-bottom: 0.5rem;
            background: var(--accent-grad);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
          }
          .header p {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 1rem;
          }
          .btn-home {
            display: inline-block;
            padding: 0.45rem 0.9rem;
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            text-decoration: none;
            border-radius: 8px;
            font-weight: 500;
            font-size: 0.85rem;
            transition: all 0.2s ease;
          }
          .btn-home:hover {
            border-color: var(--accent);
            color: var(--accent);
          }
          .count-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            background: var(--border);
            color: var(--text);
            font-size: 0.8rem;
            margin-left: 0.5rem;
            font-weight: 600;
          }
          .table-wrapper {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.05);
          }
          table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9rem;
            text-align: left;
          }
          th {
            background: var(--bg);
            padding: 0.85rem 1.25rem;
            color: var(--muted);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
          }
          td {
            padding: 0.85rem 1.25rem;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
          }
          tr:last-child td {
            border-bottom: none;
          }
          tr:hover td {
            background: rgba(138, 164, 255, 0.04);
          }
          td a {
            color: var(--accent);
            text-decoration: none;
            word-break: break-all;
          }
          td a:hover {
            text-decoration: underline;
          }
          .lastmod {
            color: var(--muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 0.82rem;
            white-space: nowrap;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <h1>XML Sitemap</h1>
            <p>
              This sitemap is generated automatically for search engines (like Google and Bing) to crawl and index all pages on this blog.
            </p>
            <a class="btn-home" href="/">← Back to Website</a>
          </div>

          <div class="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th style="width: 50px;">#</th>
                  <th>URL</th>
                  <th style="width: 150px; text-align: right;">Last Modified</th>
                </tr>
              </thead>
              <tbody>
                <xsl:for-each select="/s:urlset/s:url">
                  <tr>
                    <td style="color: var(--muted); font-size: 0.8rem;"><xsl:value-of select="position()"/></td>
                    <td>
                      <a href="{s:loc}">
                        <xsl:value-of select="s:loc"/>
                      </a>
                    </td>
                    <td style="text-align: right;">
                      <span class="lastmod">
                        <xsl:choose>
                          <xsl:when test="s:lastmod">
                            <xsl:value-of select="s:lastmod"/>
                          </xsl:when>
                          <xsl:otherwise>—</xsl:otherwise>
                        </xsl:choose>
                      </span>
                    </td>
                  </tr>
                </xsl:for-each>
              </tbody>
            </table>
          </div>
        </div>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
