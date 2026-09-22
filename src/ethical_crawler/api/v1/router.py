"""REST API v1 endpoints for the Ethical Web Crawler."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response
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
            if ai_result:
                try:
                    from ethical_crawler.vector_store import get_vector_store

                    get_vector_store().upsert_page(res, ai_data=ai_result.data)
                except Exception:
                    pass

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


@router.post("/ask", response_model=AskResponse)
async def ask_crawled_knowledge(req: AskRequest):
    """Ask an AI question answered strictly from previously crawled web pages (RAG)."""
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    res = await store.ask_crawled_knowledge(req.question, n_context=req.context_limit)
    return AskResponse(
        answer=res.get("answer", "No response generated"),
        sources=res.get("sources", []),
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
    )


@router.get("/dossier/export")
async def export_market_dossier(
    domains: str = Query(..., description="Comma-separated list of domains"),
    format: str = Query("pdf", description="Export format: pdf | md | txt"),
    model: str = Query("moonshotai/kimi-k3", description="NVIDIA NIM model to synthesize"),
    custom_focus: str | None = Query(None, description="Optional custom focus"),
):
    """Generate and immediately download an executive market dossier as PDF or Markdown."""
    d_list = [d.strip() for d in domains.split(",") if d.strip()]
    dossier_gen = DossierGenerator(default_model=model)
    dossier = await dossier_gen.generate_dossier(
        domains=d_list,
        model=model,
        custom_focus=custom_focus,
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
