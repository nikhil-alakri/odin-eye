# Summary (plain language)

This project is an **ethical web crawler**. It visits websites the way a careful researcher would: it asks permission first, waits between requests, says who it is, and prefers the site’s own map of pages when one exists.

After a visit, it keeps a **clean copy of the page text** on your computer. You can search that library by meaning, ask questions about what you collected, compare several companies, or download a page as PDF, Markdown, or a spreadsheet — without crawling the live site again.

You do not need to know Python to use the main product. Open the **dashboard in a browser** (usually http://localhost:8000), paste a website address, and press **Start Ethical Crawl**.

---

## What it is for

People use it to:

- Collect a small, respectful set of public web pages (a company site, a help center, a catalog).
- Keep those pages in a **local knowledge library** instead of copy-pasting into notes.
- Find pages later with a normal-language search (“refund policy”, “pricing”).
- Ask a question that is answered **only from pages you already collected**, with links back to the sources.
- Re-read or export an old page (PDF, text, JSON, CSV) without hitting the website again.
- Optionally pull out structured facts (product name, price, FAQs) when an AI key is configured.

It is **not** a stealth scraper, a spam bot, or a tool for ignoring a site’s rules.

---

## The four “be a good visitor” rules

These are the product’s north star. They are on by default.

1. **Check robots.txt** — many sites publish a small file that says which bots may visit which paths. This crawler reads that file before fetching a page.
2. **Wait between visits** — it pauses (about two seconds by default) so it does not hammer a server. If the site says “slow down” (HTTP 429), it waits longer.
3. **Wear a name tag** — every request includes a clear bot name, version, a public URL, and a contact email so a site owner can tell who visited.
4. **Use the sitemap when asked** — if the site publishes a list of important URLs, the crawler can follow that list instead of wandering randomly through every link.

You can turn some of these off in the form, but the honest default is “follow the rules.”

---

## What you see in the browser

Three tabs:

**Website Crawler**  
Start from a homepage (or a sitemap). Set how many pages to collect and how deep to follow links. Ready-made recipes exist for a tiny test, competitor research, filling a knowledge base, shops, JavaScript-heavy sites, and a slow “polite” crawl.

**Single Page Scraper**  
One exact URL. Useful when you already know the page you want.

**Knowledge & History**  
Everything already saved: grouped by website, with dates, size, and “this page was updated again” version numbers. From here you search, ask AI, preview, export, recrawl, or delete.

The **ChromaDB Active** chip in the header is simply “your local library is on.” Click it to see how many documents you have and which websites they came from.

---

## What gets stored (and what does not)

Saved on **your machine**, in a local folder (`data/chroma`):

- The cleaned article-like text of each page
- Title, address, date, which site it belongs to
- Optional AI notes (company profile, product fields) if you turned extraction on
- How many times you recrawled the same address, and whether the text grew or shrank

Not stored as a public cloud of other people’s sites unless **you** run the crawler and point it there. Crawl jobs that are still running live only in memory: if you restart the app mid-crawl, the job list resets, but **already-saved pages stay**.

Deleting a page or a whole domain from the dashboard is permanent for that local library. Don’t treat “Delete Domain” as undo.

---

## Optional extras (still in everyday terms)

- **Smart cache** — if you already collected a page recently (about a week), it can reuse the saved copy instead of downloading again.
- **JavaScript sites** — some pages are empty until a browser runs. The crawler can open a real (headless) browser for those.
- **Playbooks** — short click/type recipes (dismiss cookie banners, open FAQs) so the saved text matches what a person would see.
- **Market dossier** — pick several saved websites and ask the AI to write a comparison. Needs an API key.
- **Ask AI** — questions are supposed to stay grounded in *your* saved pages, not the whole internet.

Without an AI key, crawl, save, search by stored text, preview, and export still work. Chatty answers and auto-extracted “company profiles” will not.

---

## Getting started without the jargon

1. Install once (someone technical can run the setup in the project README).
2. Open http://localhost:8000
3. Paste a site you are allowed to collect.
4. Keep **Respect robots.txt** on. Start with **Quick Test** (a few pages) if you are unsure.
5. When it finishes, open **Knowledge & History** and click a domain to read what was saved.

If a site blocks bots or has no public content, you will get errors or empty pages — that is the crawler behaving, not a mysterious failure.

---

## One short technical footnote

If you later need commands, HTTP routes, file names, or environment variables, those live in the other files in this folder (`cli.md`, `api.md`, `architecture.md`, and so on). **This page is the product story.** The code story starts in `src/ethical_crawler` and is optional reading.
