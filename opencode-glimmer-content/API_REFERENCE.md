# Ethical Crawler API Reference

## 🌟 REST API Overview

**Base URL**: `http://localhost:8000/api/v1`

All API endpoints require authentication via a Bearer token in the `Authorization` header, or session cookies for the web interface.

```bash
# Example auth header
Authorization: Bearer your-session-token-or-api-key
```

---

## 📋 Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check and service status |
| `GET` | `/robots/{domain}` | Check robots.txt compliance |
| `GET` | `/sitemap/{domain}` | Fetch and parse sitemap.xml |
| `POST` | `/crawl` | Start a new crawl job |
| `GET` | `/crawl/{job_id}` | Get crawl job status |
| `POST` | `/extract` | Extract structured data from HTML |
| `POST` | `/export` | Export crawl results to format |
| `GET` | `/knowledge/{query}` | Semantic search over cached content |
| `POST` | `/ask` | AI Q&A over crawled content |
| `GET` | `/metrics` | Performance metrics and stats |
| `GET` | `/docs` | Swagger/OpenAPI UI |

---

## 🔍 Detailed Endpoints

### 1. Health Check

```http
GET /health
```

**Response (200):**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 3600.2,
  "components": {
    "redis": "connected",
    "chromadb": "connected",
    "playwright": "available",
    "http_engine": "available"
  },
  "rules": {
    "robots_txt": true,
    "politeness_delay": true,
    "identifiable_ua": true,
    "sitemap_discovery": true
  }
}
```

---

### 2. robots.txt Check

```http
GET /robots/{domain}
```

**Path parameter**: `{domain}` - e.g., `example.com`

**Response (200):**

```json
{
  "domain": "example.com",
  "robots_txt_available": true,
  "crawl_allowed": true,
  "disallowed_paths": ["/admin", "/private", "/login"],
  "allowed_paths": ["/", "/public", "/api"],
  "sitemap": "https://example.com/sitemap.xml",
  "last_checked": "2024-01-15T10:30:00Z",
  "ttl_seconds": 3600
}
```

**Response (404)**: robots.txt not found (still allowed by default, but logged)

---

### 3. Sitemap Fetch

```http
GET /sitemap/{domain}
```

**Path parameter**: `{domain}` - e.g., `example.com`

**Response (200):**

```json
{
  "domain": "example.com",
  "sitemap_available": true,
  "sitemap_url": "https://example.com/sitemap.xml",
  "sitemap_type": "xml",  # or "gz", "txt"
  "total_urls": 47,
  "urls": [
    {
      "loc": "https://example.com/page1",
      "lastmod": "2024-01-10",
      "changefreq": "weekly",
      "priority": 0.8
    }
  ],
  "last_checked": "2024-01-15T10:30:00Z"
}
```

---

### 4. Start Crawl Job

```http
POST /crawl
```

**Request body (JSON):**

```json
{
  "seed_urls": ["https://example.com"],
  "max_pages": 50,
  "max_depth": 3,
  "respect_robots_txt": true,
  "delay_between_requests": 2.0,
  "extract_ai": false,
  "schema": "article",
  "export_format": "json",
  "output_path": "./results.json"
}
```

**Response (202):**

```json
{
  "job_id": "crawl_abc123def456",
  "status": "pending",
  "message": "Crawl job queued successfully",
  "estimated_completion": "2024-01-15T11:00:00Z"
}
```

---

### 5. Get Crawl Job Status

```http
GET /crawl/{job_id}
```

**Path parameter**: `{job_id}` - e.g., `crawl_abc123def456`

**Response (200):**

```json
{
  "job_id": "crawl_abc123def456",
  "status": "running",  # pending | running | completed | failed | cancelled
  "progress": {
    "pages_crawled": 12,
    "total_pages": 50,
    "percentage": 24.0,
    "elapsed_seconds": 45.3
  },
  "statistics": {
    "url_count": 120,
    "domain_count": 3,
    "avg_response_time": 0.45,
    "status_codes": {
      "200": 9,
      "301": 2,
      "404": 1,
      "429": 0
    }
  },
  "extracted_data": {
    "title": "Example Domain",
    "headings": ["Example Domain"],
    "meta_description": "Example domain..."
  }
}
```

**Response (404)**: Job not found

---

### 6. Extract Structured Data

```http
POST /extract
```

**Request body (JSON):**

```json
{
  "html": "<html>...full page HTML...</html>",
  "schema": "article",  # article, product, faq, company, custom
  "prompt": "Extract the article title, author, and publication date",
  "include_metadata": true
}
```

**Response (200):**

```json
{
  "extracted": {
    "title": "Article Title",
    "author": "John Doe",
    "date_published": "2024-01-15",
    "body": "Full article text extracted..."
  },
  "metadata": {
    "og_title": "Open Graph Title",
    "og_description": "Open Graph description",
    "twitter_card": "summary_large_image",
    "json_ld": {
      "@context": "https://schema.org",
      "@type": "Article"
    }
  },
  "cleanliness_score": 0.92,
  "noise_removed_percentage": 87
}
```

---

### 7. Export Results

```http
POST /export
```

**Request body (JSON):**

```json
{
  "data": [...crawl results...],
  "format": "json",  # json | jsonl | markdown | plain | csv | pdf | sqlite
  "filename": "results",
  "include_metadata": true,
  "compress": false
}
```

**Response (200):**

```json
{
  "download_url": "/api/v1/files/results.json",
  "format": "json",
  "file_size_bytes": 10240,
  "records_exported": 47,
  "expires_at": "2024-01-22T10:30:00Z"
}
```

Available formats: `json`, `jsonl`, `markdown`, `plain`, `csv`, `pdf`, `sqlite`

---

### 8. Semantic Search (Knowledge Base)

```http
GET /knowledge/{query}
```

**Path parameter**: `{query}` - search query string

**Response (200):**

```json
{
  "query": "pricing plans enterprise",
  "results": [
    {
      "content": "Enterprise pricing starts at $99/month per user",
      "source_url": "https://example.com/pricing",
      "score": 0.94,
      "metadata": {
        "title": "Pricing",
        "last_modified": "2024-01-12",
        "file_type": "html"
      }
    }
  ],
  "total_results": 8,
  "search_time_ms": 12
}
```

---

### 9. AI Q&A

```http
POST /ask
```

**Request body (JSON):**

```json
{
  "question": "What are the pricing plans and refund policy?",
  "context_limit": 10,  # max number of relevant passages
  "include_sources": true,
  "model": "meta/llama-3.3-70b-instruct"
}
```

**Response (200):**

```json
{
  "answer": "Enterprise pricing starts at $99/month per user. The refund policy allows cancellations within 30 days for a full refund, no questions asked.",
  "sources": [
    {
      "content": "Enterprise pricing starts at $99/month per user",
      "source_url": "https://example.com/pricing",
      "score": 0.94
    }
  ],
  "model_used": "meta/llama-3.3-70b-instruct",
  "confidence": 0.89,
  "answer_type": "extractive"
}
```

---

### 10. Performance Metrics

```http
GET /metrics
```

**Response (200):**

```json
{
  "uptime_seconds": 86400,
  "total_crawls": 1247,
  "total_pages_extracted": 34218,
  "average_crawl_time": 2.3,
  "average_extract_time": 1.8,
  "cache_hit_rate": 0.87,
  "rate_limit_enforcements": 12,
  "robots_txt_checks": 893,
  "sitemap_lookups": 456,
  "active_crawls": 2,
  "storage": {
    "chromadb_size": 15420,
    "max_chromadb_size": 100000,
    "storage_path": "./data/chroma"
  }
}
```

---

## 🔐 Authentication

The API uses session-based authentication for the web interface and API keys for programmatic access.

### Session-based (Browser/CLI)

1. Login via `/auth/login` (POST with credentials)
2. Receive session cookie automatically set by the server
3. All subsequent requests include the session cookie

### API Key (Programmatic)

```bash
# Set the API key in the Authorization header
curl -H "Authorization: Bearer sk-abc123def456" http://localhost:8000/api/v1/health
```

**Default API key**: From `.env` `CRAWLER_API_KEY` (or generated on first login).

---

## 📊 WebSocket Events (Beta)

Real-time crawl job updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/crawl/{job_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update UI: status, progress, extracted data
};
```

Events: `status_change`, `progress_update`, `data_extracted`, `crawl_complete`

---

## 📦 Error Codes

| Code | Meaning | Notes |
|------|---------|-------|
| 200 | OK | Successful request |
| 202 | Accepted | Job queued, not yet complete |
| 400 | Bad Request | Invalid input parameters |
| 401 | Unauthorized | Missing/invalid auth |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Job/endpoint not found |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limited |
| 500 | Internal Server Error | Server bug |
| 503 | Service Unavailable | Temporary outage |

Error response format:

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Field 'max_pages' must be between 1 and 1000",
  "path": "/crawl",
  "received": 1500,
  "limit": 1000
}
```