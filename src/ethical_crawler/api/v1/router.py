"""REST API v1 endpoints for the Ethical Web Crawler."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ethical_crawler.api.deps import (
    get_app_robots_parser,
    get_app_settings,
    get_app_sitemap_parser,
)
from ethical_crawler.config import Settings
from ethical_crawler.core.robots import RobotsParser
from ethical_crawler.core.sitemap import SitemapParser
from ethical_crawler.crawler import EthicalCrawler
from ethical_crawler.extractors.ai_extractor import AIExtractor
from ethical_crawler.knowledge.dossier_generator import DossierGenerator
from ethical_crawler.rpa.models import RPAStep
from ethical_crawler.rpa.presets import get_preset_recipes
from ethical_crawler.storage import StorageExporter
from ethical_crawler.types import (
    CrawlJob,
    CrawlRequest,
    CrawlResult,
    CrawlStrategy,
    JobStatus,
    DossierExportRequest,
    MarketDossierRequest,
    MarketDossierResult,
    RobotsDirectives,
    SitemapResult,
    StructuredExtractionResult,
)

router = APIRouter(prefix="/v1", tags=["Crawler API"])

# In-memory background jobs registry
_JOBS_STORE: dict[str, CrawlJob] = {}


async def _run_background_crawl(job_id: str, request: CrawlRequest):
    """Worker task executing crawl in background."""
    job = _JOBS_STORE.get(job_id)
    if not job:
        return

    job.status = JobStatus.RUNNING
    job.current_activity = f"Starting crawl for {request.url}..."
    job.current_url = request.url

    def progress_callback(
        res: CrawlResult | None,
        current: int,
        total: int,
        activity: str = "",
        current_url: str | None = None,
    ):
        job.pages_crawled = current
        job.pages_discovered = total
        if activity:
            job.current_activity = activity
        if current_url:
            job.current_url = current_url
        if res:
            existing_idx = next((i for i, r in enumerate(job.results) if r.url == res.url), None)
            if existing_idx is not None:
                job.results[existing_idx] = res
            else:
                job.results.append(res)

    try:
        crawler = EthicalCrawler(request, on_progress=progress_callback)
        results = await crawler.run()
        job.results = results
        job.pages_crawled = len(results)
        job.status = JobStatus.COMPLETED
        job.current_activity = f"Finished crawling {len(results)} pages"
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.current_activity = f"Failed: {exc}"
        job.errors.append(str(exc))
    finally:
        job.completed_at = datetime.utcnow()


@router.post("/crawl", response_model=dict[str, str], status_code=202)
async def start_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
):
    """Start a new asynchronous ethical crawl job."""
    job_id = str(uuid.uuid4())
    job = CrawlJob(job_id=job_id, request=request, status=JobStatus.PENDING)
    _JOBS_STORE[job_id] = job

    background_tasks.add_task(_run_background_crawl, job_id, request)
    return {"job_id": job_id, "status": "started", "message": "Crawl job queued"}


@router.get("/jobs/{job_id}", response_model=CrawlJob)
async def get_job_status(job_id: str):
    """Retrieve the status and results of a crawl job."""
    job = _JOBS_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/robots", response_model=RobotsDirectives)
async def check_robots(
    url: str = Query(..., description="Target site URL"),
    robots_parser: RobotsParser = Depends(get_app_robots_parser),
    settings: Settings = Depends(get_app_settings),
):
    """Ethical Rule #1: Inspect robots.txt directives for a domain."""
    directives = await robots_parser.get_directives(url, user_agent=settings.user_agent)
    return directives


@router.get("/sitemap", response_model=SitemapResult)
async def parse_sitemap(
    url: str = Query(..., description="Website base URL or sitemap.xml URL"),
    sitemap_parser: SitemapParser = Depends(get_app_sitemap_parser),
):
    """Ethical Rule #4: Parse and retrieve all URLs from a sitemap."""
    target_url = (
        url
        if url.endswith(".xml") or url.endswith(".gz")
        else sitemap_parser.get_default_sitemap_url(url)
    )
    result = await sitemap_parser.fetch_and_parse(target_url)
    return result


class ExtractRequest(BaseModel):
    url: str
    schema_type: str = "article"
    prompt: str | None = None
    model: str | None = None
    api_key: str | None = None


@router.post("/extract", response_model=StructuredExtractionResult)
async def extract_structured_data(
    req: ExtractRequest,
    settings: Settings = Depends(get_app_settings),
):
    """AI-Native structured data extraction using NVIDIA NIM or OpenAI API."""
    ai_extractor = AIExtractor(
        api_key=req.api_key or settings.ai_api_key,
        model=req.model or settings.ai_model,
    )

    if not ai_extractor.is_available():
        raise HTTPException(
            status_code=400,
            detail="AI API key not provided. Set CRAWLER_AI_API_KEY in .env or provide in request body.",
        )

    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    cached = store.get_cached_page(req.url, max_age_days=30)
    if cached and cached[0] and cached[0].markdown:
        result = cached[0]
    else:
        # Fetch page with AUTO engine
        crawl_req = CrawlRequest(url=req.url, max_pages=1, strategy=CrawlStrategy.AUTO)
        crawler = EthicalCrawler(crawl_req)
        results = await crawler.run()

        if not results or results[0].status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch content from {req.url}: {results[0].error if results else 'No response'}",
            )
        result = results[0]

    extraction = await ai_extractor.extract_structured(
        markdown=result.markdown,
        url=req.url,
        schema_type=req.schema_type,
        custom_prompt=req.prompt,
    )

    # Save extraction back to vector store
    try:
        store.upsert_page(result, ai_data=extraction.data)
    except Exception:
        pass

    return extraction


class ScrapeRequest(BaseModel):
    url: str
    strategy: CrawlStrategy = CrawlStrategy.AUTO
    respect_robots: bool = True
    use_cache: bool = True
    cache_ttl_days: int = 7
    extract_ai: bool = False
    schema_type: str = "article"
    prompt: str | None = None
    model: str | None = None
    api_key: str | None = None
    rpa_steps: list[dict[str, Any]] = Field(default_factory=list)
    auto_dismiss_modals: bool = True
    capture_screenshot: bool = False


class ScrapeResponse(BaseModel):
    success: bool
    result: CrawlResult
    ai_extraction: StructuredExtractionResult | None = None
    error: str | None = None


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_page(
    req: ScrapeRequest,
    settings: Settings = Depends(get_app_settings),
):
    """Scrape a single web page with clean markdown conversion and optional AI extraction."""
    crawl_req = CrawlRequest(
        url=req.url,
        max_pages=1,
        max_depth=0,
        strategy=req.strategy,
        respect_robots=req.respect_robots,
        use_cache=req.use_cache,
        cache_ttl_days=req.cache_ttl_days,
        rpa_steps=req.rpa_steps,
        auto_dismiss_modals=req.auto_dismiss_modals,
        capture_screenshot=req.capture_screenshot,
    )
    crawler = EthicalCrawler(crawl_req)
    results = await crawler.run()

    if not results or results[0].status_code == 0:
        err_msg = results[0].error if results else "Scraping failed: empty result"
        raise HTTPException(status_code=502, detail=err_msg)

    res = results[0]
    ai_result = None

    if req.extract_ai:
        ai_extractor = AIExtractor(
            api_key=req.api_key or settings.ai_api_key,
            model=req.model or settings.ai_model,
        )
        if ai_extractor.is_available():
            ai_result = await ai_extractor.extract_structured(
                markdown=res.markdown,
                url=res.final_url,
                schema_type=req.schema_type,
                custom_prompt=req.prompt,
            )

    # Always ensure successful page scrape is saved/updated in ChromaDB vector store
    if res.status_code == 200:
        try:
            from ethical_crawler.vector_store import get_vector_store

            ai_data = ai_result.data if ai_result else res.ai_data
            get_vector_store().upsert_page(res, ai_data=ai_data)
        except Exception as store_err:
            logger.debug("Failed to store vector embedding for scrape: %s", store_err)

    return ScrapeResponse(
        success=res.status_code == 200,
        result=res,
        ai_extraction=ai_result,
        error=res.error,
    )


@router.get("/jobs/{job_id}/export")
async def export_job_results(
    job_id: str,
    format: str = Query("json", description="Export format: pdf | md | txt | json | csv | jsonl"),
):
    """Download results of a crawl job in the requested format (PDF, MD, TXT, JSON, CSV)."""
    job = _JOBS_STORE.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != JobStatus.COMPLETED and not job.results:
        raise HTTPException(
            status_code=400,
            detail=f"Job is currently '{job.status.value}'. Results not ready for export.",
        )

    try:
        file_bytes, media_type, default_name = StorageExporter.export_bytes(
            job.results,
            fmt=format,
            metadata={"job_id": job_id, "seed_url": job.request.url},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export error: {exc}")

    filename = f"crawl_{job_id[:8]}_{default_name}"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/scrape/export")
@router.post("/scrape/export")
async def scrape_and_export(
    url: str = Query(..., description="Target web page URL to scrape and export"),
    format: str = Query("pdf", description="Export format: pdf | md | txt | json | csv"),
    strategy: CrawlStrategy = Query(CrawlStrategy.AUTO, description="Crawling engine"),
    respect_robots: bool = Query(True, description="Respect robots.txt"),
):
    """Scrape a web page and directly download it as PDF, MD, TXT, CSV, or JSON."""
    crawl_req = CrawlRequest(
        url=url,
        max_pages=1,
        max_depth=0,
        strategy=strategy,
        respect_robots=respect_robots,
    )
    crawler = EthicalCrawler(crawl_req)
    results = await crawler.run()

    if not results or results[0].status_code == 0:
        err = results[0].error if results else "Scraping failed"
        raise HTTPException(status_code=502, detail=err)

    try:
        file_bytes, media_type, default_name = StorageExporter.export_bytes(
            results,
            fmt=format,
            metadata={"source_url": url},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export error: {exc}")

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{default_name}"'},
    )


@router.get("/history/export")
async def export_cached_page(
    url: str = Query(..., description="Target web page URL from vector store to export"),
    format: str = Query("pdf", description="Export format: pdf | md | txt | json | csv"),
):
    """Export a previously crawled page stored in ChromaDB vector database without re-crawling."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    cached = store.get_cached_page(url, max_age_days=3650)
    if not cached or not cached[0]:
        raise HTTPException(status_code=404, detail="Page not found in vector store history")

    result, ai_data = cached
    try:
        file_bytes, media_type, default_name = StorageExporter.export_bytes(
            [result],
            fmt=format,
            metadata={"source_url": url, "ai_data": ai_data},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export error: {exc}")

    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{default_name}"'},
    )


@router.get("/history/page", response_model=dict[str, Any])
async def get_cached_page_content(
    url: str = Query(..., description="Target web page URL to retrieve from vector store"),
):
    """Retrieve full markdown and metadata for a previously stored page in ChromaDB."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    cached = store.get_cached_page(url, max_age_days=3650)
    if not cached or not cached[0]:
        raise HTTPException(status_code=404, detail="Page not found in vector store history")

    result, ai_data = cached
    return {
        "result": result.model_dump(mode="json"),
        "ai_data": ai_data,
    }


@router.get("/history", response_model=list[dict[str, Any]])
async def get_crawl_history(
    limit: int = Query(50, ge=1, le=500, description="Max pages to retrieve"),
):
    """Retrieve list of all pages persistently stored in the ChromaDB vector database."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    return store.list_stored_pages(limit=limit)


@router.get("/search", response_model=list[dict[str, Any]])
async def search_crawled_knowledge(
    q: str = Query(..., description="Natural language search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    domain: str | None = Query(None, description="Optional domain filter"),
):
    """Semantic vector search across all previously crawled web pages."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    return store.semantic_search(q, n_results=limit, domain=domain)


class AskRequest(BaseModel):
    question: str
    context_limit: int = 3


class AskResponse(BaseModel):
    answer: str
    sources: list[dict[str, str]]
    cached: bool = False
    matched_question: str | None = None


@router.post("/ask", response_model=AskResponse)
async def ask_crawled_knowledge(req: AskRequest):
    """Ask an AI question answered strictly from previously crawled web pages (RAG)."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    res = await store.ask_crawled_knowledge(req.question, n_context=req.context_limit)
    return AskResponse(
        answer=res.get("answer", "No response generated"),
        sources=res.get("sources", []),
        cached=bool(res.get("cached")),
        matched_question=res.get("matched_question"),
    )


@router.get("/history/store", response_model=dict[str, Any])
async def get_vector_store_overview(
    limit: int = Query(300, ge=1, le=1000, description="Max documents to include in the mapping"),
):
    """Inspect the local ChromaDB collection: counts, field mappings, and domain → document IDs."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    return store.get_store_overview(limit=limit)


@router.get("/history/domains", response_model=list[dict[str, Any]])
async def get_domains_summary(
    limit: int = Query(200, ge=1, le=1000, description="Max domains to retrieve"),
):
    """Retrieve all crawled domains grouped with aggregated metrics and page lists."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    return store.list_domains_summary(limit=limit)


@router.get("/domains", response_model=list[dict[str, Any]], tags=["History"])
async def list_domains_alias(
    limit: int = Query(200, ge=1, le=1000, description="Max domains to retrieve"),
):
    """Convenience alias for /history/domains listing all crawled domains."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    return store.list_domains_summary(limit=limit)


@router.delete("/history/page")
async def delete_history_page(
    url: str = Query(..., description="Target page URL to delete"),
):
    """Safely delete an individual page from ChromaDB vector store."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    success = store.delete_page(url)
    if not success:
        raise HTTPException(status_code=404, detail="Page not found in vector store")
    return {"status": "deleted", "deleted": True, "url": url}


@router.delete("/history/domain")
async def delete_history_domain(
    domain: str = Query(..., description="Target domain to delete all pages for"),
):
    """Safely delete all pages under a specific domain from ChromaDB."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    count = store.delete_domain(domain)
    return {"status": "deleted", "domain": domain, "deleted_count": count}


class RecrawlRequest(BaseModel):
    url: str
    strategy: CrawlStrategy = CrawlStrategy.AUTO
    extract_ai: bool = True
    ai_schema: str = "company_profile"
    model: str | None = None


@router.post("/history/recrawl")
async def recrawl_page_live(req: RecrawlRequest):
    """Re-crawl a previously saved page live (cache off) to track revisions and growth."""
    from ethical_crawler.vector_store import get_vector_store

    crawl_req = CrawlRequest(
        url=req.url,
        max_pages=1,
        max_depth=0,
        strategy=req.strategy,
        use_cache=False,  # Force live refresh to detect updates
        extract_ai=req.extract_ai,
        ai_schema=req.ai_schema,
        ai_model=req.model,
    )
    crawler = EthicalCrawler(crawl_req)
    results = await crawler.run()
    if not results or results[0].status_code == 0:
        raise HTTPException(status_code=502, detail="Failed to fetch live page")

    res = results[0]
    store = get_vector_store()
    cached = store.get_cached_page(res.final_url or res.url)
    return {
        "status": "recrawled",
        "result": res.model_dump(mode="json"),
        "ai_data": cached[1] if cached else None,
    }


@router.post("/dossier/generate", response_model=MarketDossierResult)
async def generate_market_dossier(req: MarketDossierRequest):
    """Generate an executive market intelligence dossier across selected crawled domains."""
    dossier_gen = DossierGenerator(default_model=req.model)
    return await dossier_gen.generate_dossier(
        domains=req.domains,
        model=req.model,
        custom_focus=req.custom_focus,
        dossier_type=req.dossier_type,
    )


def _parse_domain_query(domains: list[str]) -> list[str]:
    """Accept repeated ?domains= or comma-separated values in each param."""
    out: list[str] = []
    for raw in domains:
        for part in raw.split(","):
            clean = part.strip()
            if clean:
                out.append(clean)
    return out


@router.post("/dossier/export-content")
async def export_dossier_content(req: DossierExportRequest):
    """Download PDF/Markdown for dossier text already shown in the UI (no re-generation)."""
    from ethical_crawler.types import PageMetadata

    body = req.markdown.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Markdown content is empty")

    synthetic_result = CrawlResult(
        url="https://dossier/export",
        final_url="https://dossier/export",
        status_code=200,
        title=req.title,
        markdown=body,
        cleaned_markdown_size=len(body.encode("utf-8")),
        metadata=PageMetadata(title=req.title),
    )
    fmt = req.export_format.lower().strip().lstrip(".")
    if fmt == "markdown":
        fmt = "md"

    try:
        file_bytes, media_type, _default_name = StorageExporter.export_bytes(
            [synthetic_result],
            fmt=fmt,
            metadata={"dossier": True, "export": "content"},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export error: {exc}") from exc

    ext = "md" if fmt in ("md", "markdown") else fmt
    filename = f"dossier_report.{ext}"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/dossier/export")
async def export_market_dossier(
    domains: list[str] = Query(..., description="Domain(s); repeat param or comma-separated"),
    format: str = Query("pdf", description="Export format: pdf | md | txt"),
    model: str = Query("moonshotai/kimi-k3", description="NVIDIA NIM model to synthesize"),
    custom_focus: str | None = Query(None, description="Optional custom focus"),
    dossier_type: str = Query("complete_site_report", description="Dossier template key"),
):
    """Generate and immediately download an executive market dossier as PDF or Markdown."""
    d_list = _parse_domain_query(domains)
    if not d_list:
        raise HTTPException(status_code=400, detail="At least one domain is required")
    dossier_gen = DossierGenerator(default_model=model)
    dossier = await dossier_gen.generate_dossier(
        domains=d_list,
        model=model,
        custom_focus=custom_focus,
        dossier_type=dossier_type,
    )

    from ethical_crawler.types import PageMetadata

    synthetic_result = CrawlResult(
        url=f"https://market-dossier/{'-'.join(d_list[:3])}",
        final_url=f"https://market-dossier/{'-'.join(d_list[:3])}",
        status_code=200,
        title=f"Market Intelligence Dossier - {', '.join(d_list[:3])}",
        markdown=dossier.dossier_markdown,
        metadata=PageMetadata(title=f"Market Intelligence Dossier - {', '.join(d_list[:3])}"),
    )

    try:
        file_bytes, media_type, default_name = StorageExporter.export_bytes(
            [synthetic_result],
            fmt=format,
            metadata={"dossier": True, "domains": d_list},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export error: {exc}")

    filename = f"dossier_{'_'.join(d_list[:2])}.{format}"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class RPAGenerateRequest(BaseModel):
    instruction: str
    url: str | None = None


class RPAGenerateResponse(BaseModel):
    steps: list[RPAStep]
    notes: str | None = None


@router.get("/rpa/presets", tags=["RPA Automation"])
async def list_rpa_presets():
    """List pre-built RPA interactive recipes."""
    return get_preset_recipes()


@router.post("/rpa/generate", response_model=RPAGenerateResponse, tags=["RPA Automation"])
async def generate_rpa_playbook(
    req: RPAGenerateRequest,
    settings: Settings = Depends(get_app_settings),
):
    """Generate structured RPA steps from natural language instructions using NVIDIA NIM."""
    import json

    import httpx
    from openai import AsyncOpenAI

    api_key = settings.ai_api_key
    if not api_key:
        raise HTTPException(status_code=400, detail="AI API key not configured in environment")

    client = AsyncOpenAI(
        base_url=settings.ai_base_url,
        api_key=api_key,
        timeout=httpx.Timeout(22.0, connect=6.0),
    )

    system_prompt = (
        "You are an expert web automation and Playwright RPA engineer. Given a user goal and optional target URL, "
        "output a valid JSON list of interactive automation steps to execute in headless Chromium before scraping.\n"
        "Supported actions:\n"
        "- click: {action: 'click', selector: '...', optional: true/false, wait_after_ms: 300, description: '...'}\n"
        "- fill: {action: 'fill', selector: '...', value: '...', optional: true/false, wait_after_ms: 200, description: '...'}\n"
        "- select: {action: 'select', selector: '...', value: '...', optional: true/false, wait_after_ms: 300, description: '...'}\n"
        "- wait_for: {action: 'wait_for', selector: '...', timeout_ms: 3000, optional: true/false, description: '...'}\n"
        "- press_key: {action: 'press_key', value: 'Enter'|'Escape'|'Tab', selector: '...', optional: true, description: '...'}\n"
        "- hover: {action: 'hover', selector: '...', optional: true, description: '...'}\n"
        "- scroll: {action: 'scroll', value: 'bottom'|'top'|pixels, optional: true, description: '...'}\n"
        "- sleep: {action: 'sleep', value: ms, optional: true, description: '...'}\n\n"
        "Guidelines:\n"
        "- Keep selectors resilient (prefer semantic text selectors like button:has-text('Annual'), IDs, or standard CSS).\n"
        "- Set optional: true on modal dismissals and speculative banners so they don't break the crawl.\n"
        '- Output MUST BE valid raw JSON matching: {"steps": [...], "notes": "brief summary"}.\n'
        "- Do not enclose in markdown blocks. Output raw JSON only."
    )

    user_prompt = (
        f"Target Page: {req.url or 'Dynamic Web Page'}\nDesired Action Playbook: {req.instruction}"
    )

    candidates = [
        "deepseek-ai/deepseek-v4.1-flash",
        "meta/llama-3.2-11b-vision-instruct",
        "nvidia/nemotron-3.5-lightning-30b-a3b",
    ]

    last_err = None
    for candidate in candidates:
        try:
            completion = await client.chat.completions.create(
                model=candidate,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1500,
            )
            raw_text = completion.choices[0].message.content or ""
            if not raw_text.strip() and hasattr(completion.choices[0].message, "reasoning_content"):
                raw_text = getattr(completion.choices[0].message, "reasoning_content", "") or ""

            clean_json = raw_text.strip()
            if clean_json.startswith("```"):
                lines = clean_json.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                clean_json = "\n".join(lines).strip()

            data = json.loads(clean_json)
            raw_steps = data.get("steps", [])
            parsed_steps = [RPAStep(**s) for s in raw_steps]
            return RPAGenerateResponse(steps=parsed_steps, notes=data.get("notes"))
        except Exception as exc:
            last_err = exc
            continue

    raise HTTPException(status_code=500, detail=f"Failed to generate RPA steps via AI: {last_err}")


class ElementCheckRequest(BaseModel):
    """Request model for checking CSS selectors against page HTML or URL."""

    selector: str
    html: str | None = None
    url: str | None = None


class ElementCheckResponse(BaseModel):
    """Result of checking a CSS selector against DOM elements."""

    selector: str
    match_count: int
    matches: list[dict[str, Any]]
    error: str | None = None


@router.post("/elements/check", response_model=ElementCheckResponse)
async def check_elements(
    req: ElementCheckRequest,
    settings: Settings = Depends(get_app_settings),
):
    """Test a CSS selector against provided HTML or fetched URL."""
    from ethical_crawler.extractors.element_inspector import ElementInspector

    html = req.html
    if not html and req.url:
        import httpx

        async with httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent}, timeout=15.0
        ) as client:
            resp = await client.get(req.url)
            html = resp.text

    if not html:
        raise HTTPException(status_code=400, detail="Either 'html' or 'url' must be provided")

    try:
        matches = ElementInspector.query_selector(html, req.selector)
        return ElementCheckResponse(
            selector=req.selector,
            match_count=len(matches),
            matches=matches,
        )
    except ValueError as val_err:
        return ElementCheckResponse(
            selector=req.selector,
            match_count=0,
            matches=[],
            error=str(val_err),
        )


@router.get("/elements/sandbox", response_class=HTMLResponse, tags=["Elements"])
async def get_element_picker_sandbox(
    url: str,
    settings: Settings = Depends(get_app_settings),
):
    """Serve a sandboxed version of the target page HTML with element-picker scripts injected."""
    from fastapi.responses import HTMLResponse
    from ethical_crawler.extractors.element_picker import ElementPicker

    if not url or not url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="A valid http(s) URL is required")

    html_content = ""
    import httpx

    try:
        async with httpx.AsyncClient(
            headers={"User-Agent": settings.user_agent},
            timeout=15.0,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            html_content = resp.text
    except Exception as exc:
        html_content = f"<html><body><h3>Failed to load target URL</h3><p>{exc}</p></body></html>"

    prepared_html = ElementPicker.sanitize_and_prepare_html(html_content, target_url=url)
    return HTMLResponse(
        content=prepared_html,
        headers={"X-Frame-Options": "SAMEORIGIN"},
    )


# ==============================================================================
# SCHEDULES & AUTONOMOUS MONITORS API
# ==============================================================================
from ethical_crawler.scheduler import (
    ScheduleCreateRequest,
    ScheduleJob,
    ScheduleUpdateRequest,
    get_schedule_manager,
)
from ethical_crawler.knowledge.diff_engine import ContentDiffEngine, ContentDiffResult


class DiffCompareRequest(BaseModel):
    old_text: str | None = None
    new_text: str | None = None
    url: str | None = None


@router.get("/schedules", response_model=list[ScheduleJob], tags=["Schedules"])
async def list_schedules():
    """List all configured autonomous monitors and schedules."""
    return get_schedule_manager().list_schedules()


@router.post("/schedules", response_model=ScheduleJob, tags=["Schedules"])
async def create_schedule(req: ScheduleCreateRequest):
    """Register a new URL monitor schedule."""
    return get_schedule_manager().create_schedule(req)


@router.get("/schedules/{schedule_id}", response_model=ScheduleJob, tags=["Schedules"])
async def get_schedule(schedule_id: str):
    """Get details, history, and diff summary for a specific monitor."""
    job = get_schedule_manager().get_schedule(schedule_id)
    if not job:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return job


@router.patch("/schedules/{schedule_id}", response_model=ScheduleJob, tags=["Schedules"])
async def update_schedule(schedule_id: str, req: ScheduleUpdateRequest):
    """Update a monitor's interval, webhook, or active status."""
    job = get_schedule_manager().update_schedule(schedule_id, req)
    if not job:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return job


@router.post("/schedules/{schedule_id}/toggle", response_model=ScheduleJob, tags=["Schedules"])
async def toggle_schedule(schedule_id: str):
    """Toggle a monitor between ACTIVE and PAUSED."""
    job = get_schedule_manager().toggle_schedule(schedule_id)
    if not job:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return job


@router.delete("/schedules/{schedule_id}", tags=["Schedules"])
async def delete_schedule(schedule_id: str):
    """Delete a monitor schedule."""
    success = get_schedule_manager().delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {"status": "deleted", "id": schedule_id}


@router.post("/schedules/{schedule_id}/run", tags=["Schedules"])
async def run_schedule_now(schedule_id: str):
    """Trigger an immediate out-of-schedule execution of a monitor."""
    job, diff = await get_schedule_manager().execute_job(schedule_id)
    if not job:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return {
        "status": "completed",
        "job": job,
        "diff": diff,
    }


@router.post("/diff", response_model=ContentDiffResult, tags=["Schedules"])
async def compare_content_diff(req: DiffCompareRequest):
    """Compare two texts or compare a URL's latest text with its stored historical snapshot."""
    old_text = req.old_text
    new_text = req.new_text

    if req.url and (old_text is None or new_text is None):
        cached = get_vector_store().get_cached_page(req.url, max_age_days=365)
        if cached and isinstance(cached, tuple):
            cached_res, _ = cached
            old_text = cached_res.markdown if cached_res else None

    return ContentDiffEngine.compute_diff(
        old_text, new_text, old_label="Historical Snapshot", new_label="Latest Content"
    )


# ==============================================================================
# VISION & MULTIMODAL EXTRACTION API (Feature 2)
# ==============================================================================
from ethical_crawler.extractors.pdf_extractor import PDFExtractor, PDFParseResult
from ethical_crawler.extractors.vision_extractor import (
    VisionExtractor,
    VisionExtractRequest,
    VisionExtractResult,
)


class PDFParseRequest(BaseModel):
    url: str
    index_in_chroma: bool = True
    parent_url: str | None = None


@router.get("/screenshots", tags=["Vision"])
async def list_screenshots(domain: str | None = None):
    """List archived page screenshots partitioned by domain."""
    base_dir = Path("data/screenshots")
    if not base_dir.exists():
        return []

    results: list[dict[str, Any]] = []
    target_dirs = [base_dir / domain] if domain else [d for d in base_dir.iterdir() if d.is_dir()]

    valid_exts = {".png", ".jpg", ".jpeg", ".webp"}
    for d in target_dirs:
        if not d.exists() or not d.is_dir():
            continue
        domain_name = d.name
        img_files = [f for f in d.iterdir() if f.is_file() and f.suffix.lower() in valid_exts]
        for f in sorted(img_files, key=lambda x: x.stat().st_mtime, reverse=True):
            stat = f.stat()
            results.append({
                "domain": domain_name,
                "filename": f.name,
                "url_path": f"/api/v1/screenshots/file/{domain_name}/{f.name}",
                "size_bytes": stat.st_size,
                "captured_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            })

    return results


@router.get("/screenshots/file/{domain}/{filename}", tags=["Vision"])
async def get_screenshot_file(domain: str, filename: str):
    """Stream a captured screenshot image file."""
    clean_domain = Path(domain).name
    clean_filename = Path(filename).name

    target_file = Path("data/screenshots") / clean_domain / clean_filename
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")

    content = target_file.read_bytes()
    suffix = target_file.suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/webp" if suffix == ".webp" else "image/jpeg"
    return Response(content=content, media_type=media_type)


@router.post("/vision/extract", response_model=VisionExtractResult, tags=["Vision"])
async def extract_vision_insights(req: VisionExtractRequest):
    """Extract structured data, tables, or executive summaries from an image/screenshot using Vision LLM."""
    return await VisionExtractor.extract(req)


@router.post("/pdf/parse", response_model=PDFParseResult, tags=["Vision"])
async def parse_pdf_document(req: PDFParseRequest):
    """Download, parse, and optionally index a PDF document into ChromaDB vector knowledge."""
    return await PDFExtractor.extract_from_url(
        url=req.url,
        index_in_chroma=req.index_in_chroma,
        parent_url=req.parent_url,
    )


# ==============================================================================
# COMPETITIVE INTELLIGENCE & TECHNOLOGY PROFILING API
# ==============================================================================
from ethical_crawler.extractors.tech_profiler import TechnologyProfiler, TechProfileResult
from ethical_crawler.knowledge.competitor_comparator import (
    CompetitorComparator,
    CompetitorComparisonResult,
)


class TechProfileRequest(BaseModel):
    url: str | None = None
    headers: dict[str, str] | None = None
    html: str | None = None


class CompetitorCompareRequest(BaseModel):
    domains: list[str] = Field(..., min_length=2, max_length=5)
    custom_focus: str | None = None


class CompetitorExportRequest(BaseModel):
    domains: list[str] = Field(..., min_length=2, max_length=5)
    custom_focus: str | None = None
    format: str = Field(default="pdf")


@router.post("/tech-profile", response_model=TechProfileResult, tags=["Competitive Intelligence"])
async def profile_technology_stack(
    req: TechProfileRequest,
    settings: Settings = Depends(get_app_settings),
):
    """Passively fingerprint technology stack (Frameworks, CMS, Analytics, CDN/Infra) from headers or HTML."""
    if req.url and not req.html:
        return await TechnologyProfiler.profile_url(req.url, user_agent=settings.user_agent)
    return TechnologyProfiler.profile(
        headers=req.headers,
        html=req.html,
        url=req.url,
    )


@router.post("/competitors/compare", response_model=CompetitorComparisonResult, tags=["Competitive Intelligence"])
async def compare_competitors(req: CompetitorCompareRequest):
    """Generate a multi-domain competitive benchmarking matrix across 2-5 indexed domains."""
    try:
        comparator = CompetitorComparator()
        return await comparator.compare_domains(
            domains=req.domains,
            custom_focus=req.custom_focus,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Competitor comparison failed: {exc}")


@router.post("/competitors/compare/export", tags=["Competitive Intelligence"])
async def export_competitor_comparison(req: CompetitorExportRequest):
    """Export multi-domain competitive comparison report as styled PDF or Markdown download."""
    try:
        comparator = CompetitorComparator()
        res = await comparator.compare_domains(
            domains=req.domains,
            custom_focus=req.custom_focus,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {exc}")

    domain_tag = "_vs_".join(d.replace(".", "_") for d in req.domains[:3])
    fmt = req.format.lower().strip()

    if fmt in ["markdown", "md"]:
        return Response(
            content=res.full_report_md,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="competitor_report_{domain_tag}.md"'
            },
        )

    # Default to PDF
    import io
    buf = io.BytesIO()
    pdf_bytes = CompetitorComparator.export_pdf(res, buf)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="competitor_report_{domain_tag}.pdf"'
        },
    )


# ==============================================================================
# VISUAL PRODUCT BLUEPRINT & REVERSE-ENGINEERING API
# ==============================================================================
from ethical_crawler.extractors.visual_blueprint_generator import (
    ProductBlueprintResult,
    VisualBlueprintGenerator,
)


class BlueprintGenerateRequest(BaseModel):
    domain: str
    custom_focus: str | None = None
    model: str | None = None


class BlueprintExportRequest(BaseModel):
    domain: str
    custom_focus: str | None = None
    model: str | None = None
    format: str = Field(default="pdf")
    dossier_markdown: str | None = None
    blueprint_data: dict[str, Any] | None = None


class BlueprintUploadItem(BaseModel):
    filename: str
    data_base64: str


class BlueprintUploadRequest(BaseModel):
    domain: str
    files: list[BlueprintUploadItem]


@router.get("/blueprint/domains", tags=["Visual Blueprint"])
async def get_blueprint_domains():
    """List all domains that have captured screenshot archives available for blueprinting."""
    generator = VisualBlueprintGenerator()
    return generator.list_available_domains()


@router.post("/blueprint/generate", response_model=ProductBlueprintResult, tags=["Visual Blueprint"])
async def generate_product_blueprint(req: BlueprintGenerateRequest):
    """Generate a complete full-stack product specification and architectural blueprint from screenshots."""
    try:
        generator = VisualBlueprintGenerator()
        return await generator.generate_blueprint(
            domain=req.domain,
            custom_focus=req.custom_focus,
            model=req.model,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate blueprint: {exc}")


@router.post("/blueprint/export", tags=["Visual Blueprint"])
async def export_product_blueprint(req: BlueprintExportRequest):
    """Download the complete product architecture blueprint as an executive styled PDF or Markdown file."""
    domain_tag = req.domain.replace(".", "_")
    fmt = req.format.lower().strip()

    # Markdown export
    if fmt in ["markdown", "md"]:
        dossier_md = req.dossier_markdown
        if not dossier_md:
            if req.blueprint_data:
                dossier_md = req.blueprint_data.get("full_markdown_dossier", "")
            if not dossier_md:
                generator = VisualBlueprintGenerator()
                res = await generator.generate_blueprint(
                    domain=req.domain,
                    custom_focus=req.custom_focus,
                    model=req.model,
                )
                dossier_md = res.full_markdown_dossier
        return Response(
            content=dossier_md,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="blueprint_{domain_tag}.md"'
            },
        )

    # Executive Styled PDF Export
    import io
    buf = io.BytesIO()

    try:
        blueprint_obj: ProductBlueprintResult | None = None
        if req.blueprint_data:
            blueprint_obj = ProductBlueprintResult.model_validate(req.blueprint_data)
        elif not req.dossier_markdown:
            generator = VisualBlueprintGenerator()
            blueprint_obj = await generator.generate_blueprint(
                domain=req.domain,
                custom_focus=req.custom_focus,
                model=req.model,
            )

        if blueprint_obj:
            pdf_bytes = VisualBlueprintGenerator.export_pdf(blueprint_obj, buf)
        else:
            # Fallback if only raw markdown text is provided
            from ethical_crawler.storage import StorageExporter
            pdf_bytes = StorageExporter.to_dossier_pdf(
                markdown=req.dossier_markdown or "",
                title=f"Product Architecture Blueprint: {req.domain}",
                target_path_or_buf=buf,
            )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate blueprint for export: {exc}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="blueprint_{domain_tag}.pdf"'
        },
    )


@router.post("/blueprint/upload", tags=["Visual Blueprint"])
async def upload_blueprint_screenshots(req: BlueprintUploadRequest):
    """Upload screenshot files for a domain to data/screenshots/{domain}/."""
    import base64
    from urllib.parse import urlparse
    import re

    clean_domain = req.domain.strip().lower()
    if clean_domain.startswith("http://") or clean_domain.startswith("https://"):
        clean_domain = urlparse(clean_domain).netloc.lower()
    clean_domain = clean_domain.split("/")[0].strip()
    if not clean_domain:
        raise HTTPException(status_code=400, detail="Domain or project name is required")

    clean_domain = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", clean_domain)
    target_dir = Path("data/screenshots") / clean_domain
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for item in req.files:
        fn = Path(item.filename).name
        fn = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", fn)
        if not any(fn.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp"]):
            fn = f"{fn}.png"

        raw_b64 = item.data_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]

        try:
            img_bytes = base64.b64decode(raw_b64)
            file_path = target_dir / fn
            file_path.write_bytes(img_bytes)
            saved_files.append(fn)
        except Exception as exc:
            logger.warning(f"Failed to decode or write image {fn}: {exc}")

    return {
        "status": "success",
        "domain": clean_domain,
        "saved_count": len(saved_files),
        "files": saved_files,
    }


