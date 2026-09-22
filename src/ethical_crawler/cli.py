"""Interactive Command Line Interface (Typer + Rich).

Commands for ethical crawling, sitemap discovery, robots.txt verification,
AI-powered structured extraction, and starting the web service.
"""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from ethical_crawler.config import get_settings
from ethical_crawler.core.robots import get_robots_parser
from ethical_crawler.core.sitemap import get_sitemap_parser
from ethical_crawler.crawler import EthicalCrawler
from ethical_crawler.extractors.ai_extractor import AIExtractor
from ethical_crawler.storage import StorageExporter
from ethical_crawler.types import CrawlRequest, CrawlStrategy

app = typer.Typer(
    name="ethical-crawler",
    help="AI-Native Ethical Web Crawler adhering to the 4 rules of ethical web crawling.",
    add_completion=False,
)
console = Console()


def print_banner():
    """Display startup header."""
    settings = get_settings()
    panel = Panel.fit(
        f"[bold cyan]Ethical AI-Native Web Crawler[/bold cyan]\n"
        f"[dim]Bot Identity:[/dim] [green]{settings.user_agent}[/green]\n"
        f"[dim]Rules:[/dim] [yellow]1. robots.txt[/yellow] | [yellow]2. Politeness Delay[/yellow] | "
        f"[yellow]3. Identifiable UA[/yellow] | [yellow]4. Sitemap[/yellow]",
        border_style="cyan",
    )
    console.print(panel)


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Initial URL or Sitemap URL to crawl"),
    max_pages: int = typer.Option(10, "--max-pages", "-n", help="Maximum pages to crawl"),
    max_depth: int = typer.Option(2, "--max-depth", "-d", help="Maximum crawl depth"),
    delay: float | None = typer.Option(
        None, "--delay", "-s", help="Delay between requests (seconds)"
    ),
    strategy: str = typer.Option(
        "auto", "--strategy", help="Engine strategy: auto | http | browser"
    ),
    sitemap: bool = typer.Option(
        False, "--sitemap", "-m", help="Discover and crawl URLs from sitemap.xml"
    ),
    output: str | None = typer.Option(
        None, "--output", "-o", help="File to save results (.json, .csv, .md, .txt, .pdf, .db)"
    ),
    format: str | None = typer.Option(
        None, "--format", "-f", help="Export format: pdf | md | txt | json | csv | sqlite"
    ),
    cache: bool = typer.Option(
        True, "--cache/--no-cache", help="Check local vector store cache to avoid re-crawling"
    ),
):
    """Crawl a website ethically with queue management and markdown extraction."""
    print_banner()

    try:
        strat_enum = CrawlStrategy(strategy.lower())
    except ValueError:
        console.print(f"[red]Invalid strategy '{strategy}'. Use: auto, http, or browser[/red]")
        raise typer.Exit(1)

    req = CrawlRequest(
        url=url,
        max_pages=max_pages,
        max_depth=max_depth,
        delay=delay,
        strategy=strat_enum,
        use_sitemap=sitemap,
        use_cache=cache,
    )

    table = Table(title="Crawled Pages", show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("Status", width=8)
    table.add_column("Title / URL", style="cyan")
    table.add_column("Engine", width=8)
    table.add_column("Size", justify="right", width=10)
    table.add_column("Duration", justify="right", width=8)

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Crawling...", total=max_pages)

        def on_progress(result, current_count, total_queued):
            status_color = "green" if result.status_code == 200 else "red"
            title_display = result.title or result.final_url
            if len(title_display) > 55:
                title_display = title_display[:52] + "..."

            table.add_row(
                str(current_count),
                f"[{status_color}]{result.status_code}[/{status_color}]",
                title_display,
                result.strategy_used.value,
                f"{result.cleaned_markdown_size:,} B",
                f"{result.elapsed_seconds:.2f}s",
            )
            progress.update(task, completed=current_count)

        crawler = EthicalCrawler(req, on_progress=on_progress)
        results = asyncio.run(crawler.run())

    console.print(table)
    console.print(f"[bold green]Successfully crawled {len(results)} pages.[/bold green]")

    target_file = output
    if not target_file and format:
        target_file = f"crawl_results.{format.lower().strip('.')}"
    elif target_file and format and "." not in Path(target_file).name:
        target_file = f"{target_file}.{format.lower().strip('.')}"

    if target_file:
        out_path = StorageExporter.save_file(
            results,
            target_file,
            metadata={"seed_url": url, "strategy": strategy, "max_pages": max_pages},
        )
        console.print(f"[bold blue]Results exported to:[/bold blue] {out_path}")


@app.command()
def scrape(
    url: str = typer.Argument(..., help="Single web page URL to scrape"),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="File to save results (e.g. page.pdf, page.md, page.txt, page.json)",
    ),
    format: str | None = typer.Option(
        None, "--format", "-f", help="Export format: pdf | md | txt | json | csv"
    ),
    strategy: str = typer.Option(
        "auto", "--strategy", "-s", help="Engine strategy: auto | http | browser"
    ),
    extract_ai: bool = typer.Option(
        False, "--extract-ai", "-a", help="Run AI structured extraction alongside scraping"
    ),
    schema: str = typer.Option(
        "article", "--schema", help="AI schema: article | product | faq | custom"
    ),
    prompt: str | None = typer.Option(
        None, "--prompt", "-p", help="Custom extraction prompt for AI"
    ),
    model: str | None = typer.Option(None, "--model", "-m", help="AI model name"),
    api_key: str | None = typer.Option(None, "--api-key", help="API key for AI extraction"),
    respect_robots: bool = typer.Option(
        True, "--respect-robots/--no-respect-robots", help="Check robots.txt permissions"
    ),
    cache: bool = typer.Option(
        True, "--cache/--no-cache", help="Check local vector store cache to avoid re-scraping"
    ),
):
    """Scrape a single web page, clean content into markdown/text, and export to PDF, MD, TXT, JSON, or CSV."""
    print_banner()

    try:
        strat_enum = CrawlStrategy(strategy.lower())
    except ValueError:
        console.print(f"[red]Invalid strategy '{strategy}'. Use: auto, http, or browser[/red]")
        raise typer.Exit(1)

    req = CrawlRequest(
        url=url,
        max_pages=1,
        max_depth=0,
        strategy=strat_enum,
        respect_robots=respect_robots,
        use_cache=cache,
    )

    console.print(f"[cyan]Scraping page:[/cyan] {url} (Strategy: {strategy})...")
    crawler = EthicalCrawler(req)
    results = asyncio.run(crawler.run())

    if not results or results[0].status_code == 0:
        err = results[0].error if results else "Unknown error"
        console.print(f"[bold red]Failed to scrape page:[/bold red] {err}")
        raise typer.Exit(1)

    res = results[0]
    status_color = "green" if res.status_code == 200 else "red"

    # Display overview table
    summary_table = Table(title="Scrape Summary", show_header=False, border_style="cyan")
    summary_table.add_column("Property", style="bold")
    summary_table.add_column("Value", style="dim")

    summary_table.add_row("URL", res.final_url)
    summary_table.add_row("Status", f"[{status_color}]{res.status_code}[/{status_color}]")
    summary_table.add_row("Title", res.title or "(None)")
    summary_table.add_row("Engine Used", res.strategy_used.value)
    summary_table.add_row("Markdown Size", f"{res.cleaned_markdown_size:,} bytes")
    summary_table.add_row(
        "Links Found",
        f"{len(res.internal_links)} internal, {len(res.external_links)} external",
    )
    summary_table.add_row("Elapsed Time", f"{res.elapsed_seconds:.2f}s")
    console.print(summary_table)

    # Optional AI structured extraction
    ai_data = None
    if extract_ai:
        settings = get_settings()
        extractor = AIExtractor(
            api_key=api_key or settings.ai_api_key,
            model=model or settings.ai_model,
        )
        if not extractor.is_available():
            console.print("[yellow]AI extraction skipped: No API key configured.[/yellow]")
        else:
            console.print(f"[cyan]Running AI extraction ({schema})...[/cyan]")
            extraction = asyncio.run(
                extractor.extract_structured(
                    markdown=res.markdown,
                    url=res.final_url,
                    schema_type=schema,
                    custom_prompt=prompt,
                )
            )
            ai_data = extraction.data
            # Save AI extraction into vector store
            try:
                from ethical_crawler.vector_store import get_vector_store

                get_vector_store().upsert_page(res, ai_data=ai_data)
            except Exception as store_err:
                console.print(f"[dim]Failed to update vector cache with AI data: {store_err}[/dim]")

            import json

            json_str = json.dumps(ai_data, indent=2)
            console.print(
                Panel(
                    Syntax(json_str, "json", theme="monokai", line_numbers=True),
                    title=f"AI Extracted Data ({extraction.model_used})",
                    border_style="green",
                )
            )

    # Export handling
    target_file = output
    if not target_file and format:
        target_file = f"scraped_page.{format.lower().strip('.')}"
    elif target_file and format and "." not in Path(target_file).name:
        target_file = f"{target_file}.{format.lower().strip('.')}"

    if target_file:
        out_path = StorageExporter.save_file(
            results,
            target_file,
            metadata={"seed_url": url, "strategy": strategy, "ai_extracted": ai_data is not None},
        )
        console.print(
            f"[bold green]Results successfully exported to:[/bold green] [cyan]{out_path}[/cyan]"
        )
    else:
        # Show content preview if no file was exported
        preview_text = res.markdown[:800] + (
            "\n\n[dim]...(content truncated)...[/dim]" if len(res.markdown) > 800 else ""
        )
        console.print(
            Panel(
                preview_text or "[dim](No text extracted)[/dim]",
                title="Markdown Content Preview",
                border_style="blue",
            )
        )
        console.print(
            "[dim]Tip: Use --output <file.pdf|.md|.txt|.json|.csv> or --format <fmt> to export.[/dim]"
        )


@app.command()
def search(
    query: str = typer.Argument(
        ..., help="Search query to semantically match across crawled pages"
    ),
    limit: int = typer.Option(5, "--limit", "-n", help="Max results to return"),
    domain: str | None = typer.Option(None, "--domain", "-d", help="Filter by specific domain"),
):
    """Semantic vector search across all previously crawled web pages."""
    print_banner()
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    console.print(f'[cyan]Searching crawled knowledge for:[/cyan] [bold]"{query}"[/bold]...')
    matches = store.semantic_search(query, n_results=limit, domain=domain)

    if not matches:
        console.print(
            "[yellow]No matching pages found in vector store. Crawl or scrape some websites first![/yellow]"
        )
        return

    table = Table(
        title=f"Semantic Search Results ({len(matches)} found)",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Similarity", justify="right", width=10)
    table.add_column("Title / URL", style="cyan")
    table.add_column("Snippet Preview", style="dim")

    for idx, m in enumerate(matches, 1):
        sim_pct = f"{int(m['similarity'] * 100)}%"
        table.add_row(
            str(idx),
            f"[green]{sim_pct}[/green]",
            f"[bold]{m['title']}[/bold]\n[dim]{m['final_url']}[/dim]",
            m["snippet"][:120] + "..." if len(m["snippet"]) > 120 else m["snippet"],
        )

    console.print(table)


@app.command()
def ask(
    question: str = typer.Argument(..., help="Question to ask based on crawled websites"),
    context_limit: int = typer.Option(
        3, "--context", "-c", help="Number of relevant pages to use as context"
    ),
):
    """Ask an AI question answered strictly from previously crawled web pages (RAG)."""
    print_banner()
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    console.print(f'[cyan]Querying crawled knowledge:[/cyan] [bold]"{question}"[/bold]...')

    with console.status("[bold cyan]Retrieving context & generating AI response..."):
        res = asyncio.run(store.ask_crawled_knowledge(question, n_context=context_limit))

    console.print(
        Panel(
            res["answer"],
            title="AI Answer (Grounded in Crawled Pages)",
            border_style="green",
        )
    )

    if res.get("sources"):
        console.print("[bold cyan]Cited Sources:[/bold cyan]")
        for s in res["sources"]:
            console.print(f"  • [underline]{s['title']}[/underline]: {s['url']}")


@app.command()
def history(
    limit: int = typer.Option(50, "--limit", "-n", help="Maximum pages to display"),
):
    """List all pages currently saved in the local ChromaDB vector store."""
    print_banner()
    from ethical_crawler.vector_store import get_vector_store

    store = get_vector_store()
    pages = store.list_stored_pages(limit=limit)

    if not pages:
        console.print(
            "[yellow]Vector store is currently empty. Run 'crawler scrape <url>' to save pages![/yellow]"
        )
        return

    table = Table(
        title=f"Saved Crawl History ({len(pages)} unique pages)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("Status", width=8)
    table.add_column("Title / URL", style="cyan")
    table.add_column("Engine", width=8)
    table.add_column("Size", justify="right", width=10)
    table.add_column("Crawled At", style="dim", width=20)

    for idx, p in enumerate(pages, 1):
        status_color = "green" if p.get("status_code") == 200 else "red"
        date_str = p.get("crawled_at", "")[:19].replace("T", " ")
        table.add_row(
            str(idx),
            f"[{status_color}]{p.get('status_code', 200)}[/{status_color}]",
            f"[bold]{p.get('title')}[/bold]\n[dim]{p.get('final_url')}[/dim]",
            p.get("strategy", "http"),
            f"{p.get('size', 0):,} B",
            date_str,
        )

    console.print(table)


@app.command()
def sitemap(
    url: str = typer.Argument(..., help="Base website URL or direct sitemap.xml URL"),
    output: str | None = typer.Option(
        None, "--output", "-o", help="File to export URLs (.json, .csv)"
    ),
):
    """Ethical Rule 4: Parse and inspect sitemap.xml directly."""
    print_banner()
    parser = get_sitemap_parser()
    target_url = (
        url if url.endswith(".xml") or url.endswith(".gz") else parser.get_default_sitemap_url(url)
    )

    console.print(f"[cyan]Fetching and parsing sitemap:[/cyan] {target_url}...")
    res = asyncio.run(parser.fetch_and_parse(target_url))

    if res.error:
        console.print(f"[bold red]Sitemap error:[/bold red] {res.error}")
        return

    table = Table(
        title=f"Sitemap URLs ({res.total_urls} found)", show_header=True, header_style="bold green"
    )
    table.add_column("#", style="dim", width=4)
    table.add_column("URL", style="cyan")
    table.add_column("Last Modified", width=22)
    table.add_column("Priority", justify="right", width=8)

    for idx, u in enumerate(res.urls[:25], 1):
        table.add_row(
            str(idx),
            u.loc,
            u.lastmod or "-",
            f"{u.priority:.1f}" if u.priority is not None else "-",
        )

    console.print(table)
    if res.total_urls > 25:
        console.print(f"[dim]... and {res.total_urls - 25} more URLs.[/dim]")

    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        if output.endswith(".csv"):
            import csv

            with open(output, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["URL", "Last Modified", "Change Frequency", "Priority"])
                for u in res.urls:
                    writer.writerow([u.loc, u.lastmod, u.changefreq, u.priority])
        else:
            import json

            data = [u.model_dump() for u in res.urls]
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        console.print(f"[bold blue]Saved sitemap URLs to:[/bold blue] {output}")


@app.command()
def robots(
    url: str = typer.Argument(..., help="Website URL to inspect robots.txt"),
    check_path: str | None = typer.Option(
        None, "--check", "-c", help="Specific path to check permission for"
    ),
):
    """Ethical Rule 1: Check robots.txt directives and path permissions."""
    print_banner()
    parser = get_robots_parser()
    settings = get_settings()

    console.print(f"[cyan]Inspecting robots.txt for:[/cyan] {url}...")
    directives = asyncio.run(parser.get_directives(url, user_agent=settings.user_agent))

    table = Table(
        title=f"Robots Directives: {directives.domain}",
        show_header=True,
        header_style="bold yellow",
    )
    table.add_column("Property", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Robots URL", directives.robots_url)
    table.add_row("HTTP Status", str(directives.status_code))
    table.add_row(
        "Crawl-Delay", f"{directives.crawl_delay}s" if directives.crawl_delay else "None specified"
    )
    table.add_row(
        "Sitemaps Found", "\n".join(directives.sitemaps) if directives.sitemaps else "None"
    )

    console.print(table)

    if check_path:
        full_test_url = url.rstrip("/") + "/" + check_path.lstrip("/")
        allowed = asyncio.run(parser.can_fetch(full_test_url, user_agent=settings.user_agent))
        status_text = (
            "[bold green]ALLOWED[/bold green]" if allowed else "[bold red]DISALLOWED[/bold red]"
        )
        console.print(f"Path permission for '{check_path}': {status_text}")


@app.command()
def extract(
    url: str = typer.Argument(..., help="URL to crawl and extract structured data from"),
    schema: str = typer.Option(
        "article", "--schema", "-s", help="Schema: article | product | faq | custom"
    ),
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="Custom extraction instruction"),
    model: str | None = typer.Option(
        None, "--model", "-m", help="LLM Model (e.g. meta/llama-3.3-70b-instruct)"
    ),
    api_key: str | None = typer.Option(None, "--api-key", help="API Key for NVIDIA NIM or OpenAI"),
    output: str | None = typer.Option(None, "--output", "-o", help="Save extracted JSON to file"),
):
    """AI-Native Extraction using NVIDIA NIM or OpenAI API."""
    print_banner()
    settings = get_settings()
    extractor = AIExtractor(
        api_key=api_key or settings.ai_api_key, model=model or settings.ai_model
    )

    if not extractor.is_available():
        console.print(
            "[bold red]AI API key is not configured.[/bold red]\n"
            "Please set [yellow]CRAWLER_AI_API_KEY[/yellow] in your .env file or pass [yellow]--api-key[/yellow].\n"
            "You can use NVIDIA NIM (e.g. meta/llama-3.3-70b-instruct) or OpenAI."
        )
        raise typer.Exit(1)

    console.print(f"[cyan]Fetching page content:[/cyan] {url}...")
    req = CrawlRequest(url=url, max_pages=1, strategy=CrawlStrategy.AUTO)
    crawler = EthicalCrawler(req)
    results = asyncio.run(crawler.run())

    if not results or results[0].status_code != 200:
        console.print(
            f"[bold red]Failed to fetch page:[/bold red] {results[0].error if results else 'No response'}"
        )
        raise typer.Exit(1)

    result = results[0]
    console.print(f"[cyan]Running AI structured extraction ({schema})...[/cyan]")
    extraction = asyncio.run(
        extractor.extract_structured(
            markdown=result.markdown,
            url=url,
            schema_type=schema,
            custom_prompt=prompt,
        )
    )

    import json

    json_str = json.dumps(extraction.data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
    console.print(
        Panel(syntax, title=f"AI Extracted Data ({extraction.model_used})", border_style="green")
    )

    if extraction.notes:
        console.print(f"[yellow]Notes: {', '.join(extraction.notes)}[/yellow]")

    if output:
        Path(output).write_text(json_str, encoding="utf-8")
        console.print(f"[bold blue]Saved JSON to:[/bold blue] {output}")


@app.command("parse-image")
def parse_image(
    image_path: str = typer.Argument(
        ..., help="Path to image (screenshot, PDF scan, chart) to parse"
    ),
    task: str = typer.Option(
        "markdown_bbox", "--task", "-t", help="Task: markdown_bbox | detection_only"
    ),
):
    """Visual Document Parsing using NVIDIA Nemotron-Parse 2.0."""
    print_banner()
    from ethical_crawler.extractors.nemotron_parser import NemotronParser

    parser = NemotronParser()
    if not parser.is_available():
        console.print("[bold red]NVIDIA API key not configured in .env[/bold red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Parsing image with Nemotron-Parse 2.0:[/cyan] {image_path}...")
    try:
        res = asyncio.run(parser.parse_image(image_path, task=task))
        console.print(
            Panel(
                res["raw_output"] or "[dim](No text detected)[/dim]",
                title="Nemotron-Parse 2.0 Output",
                border_style="cyan",
            )
        )
    except Exception as exc:
        console.print(f"[bold red]Failed to parse image:[/bold red] {exc}")
        raise typer.Exit(1)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host address to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the FastAPI Web Server and interactive UI dashboard."""
    print_banner()
    console.print(
        f"[bold green]Starting Web Dashboard & REST API at http://{host}:{port}[/bold green]"
    )
    console.print("[dim]Swagger API Docs available at http://localhost:8000/docs[/dim]")
    import uvicorn

    uvicorn.run("ethical_crawler.api.app:app", host=host, port=port, reload=reload)


def main():
    app()


if __name__ == "__main__":
    main()
