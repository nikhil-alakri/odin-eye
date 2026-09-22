"""Shared test fixtures and sample data."""

SAMPLE_ROBOTS_TXT = """
User-agent: *
Disallow: /admin/
Disallow: /private/
Allow: /admin/public/
Crawl-delay: 3.5
Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap_news.xml.gz

User-agent: BadBot
Disallow: /

User-agent: EthicalCrawlerBot
Disallow: /secret/
Allow: /secret/open/
Crawl-delay: 1.0
"""

SAMPLE_HTML = """<!DOCTYPE html>
<html>
<head>
    <title>Sample Test Article - Tech News</title>
    <meta name="description" content="An in-depth article about modern ethical web crawling.">
    <meta name="author" content="Jane Doe">
    <meta property="og:title" content="Ethical Crawling Guide">
    <meta property="og:description" content="Guide to respectful web scraping.">
    <link rel="canonical" href="https://example.com/guide">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Ethical Crawling Guide",
        "author": "Jane Doe"
    }
    </script>
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
    </nav>
    <div class="ad">Buy our amazing product now!</div>
    <main>
        <h1>Ethical Crawling in 2026</h1>
        <p>Web scraping should always follow politeness guidelines and respect site owners.</p>
        <p>Here are key internal links:</p>
        <ul>
            <li><a href="/docs/robots">Robots Guide</a></li>
            <li><a href="/docs/delays?utm_source=twitter&utm_medium=social">Rate Limiting</a></li>
            <li><a href="https://other-domain.org/external">External Site</a></li>
            <li><a href="/downloads/manual.pdf">PDF Manual</a></li>
            <li><a href="mailto:admin@example.com">Email Us</a></li>
        </ul>
    </main>
    <footer>
        <p>&copy; 2026 Example Corp</p>
    </footer>
</body>
</html>
"""

SAMPLE_SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <url>
      <loc>https://example.com/</loc>
      <lastmod>2026-01-01</lastmod>
      <changefreq>monthly</changefreq>
      <priority>1.0</priority>
   </url>
   <url>
      <loc>https://example.com/about</loc>
      <lastmod>2026-02-15</lastmod>
      <changefreq>yearly</changefreq>
      <priority>0.8</priority>
   </url>
   <url>
      <loc>https://example.com/contact</loc>
      <lastmod>2026-03-01</lastmod>
      <changefreq>monthly</changefreq>
      <priority>0.5</priority>
   </url>
</urlset>
"""

SAMPLE_SITEMAP_INDEX_XML = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <sitemap>
      <loc>https://example.com/sitemap_pages.xml</loc>
      <lastmod>2026-01-01</lastmod>
   </sitemap>
   <sitemap>
      <loc>https://example.com/sitemap_posts.xml</loc>
      <lastmod>2026-02-01</lastmod>
   </sitemap>
</sitemapindex>
"""
