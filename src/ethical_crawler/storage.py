"""Storage and export handlers for crawl results.

Supports JSON (with metadata envelope), JSONL, Markdown, Plain Text, CSV, PDF, and SQLite.
"""

import csv
import io
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from ethical_crawler.types import CrawlResult

# ReportLab imports for styled PDF export
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class StorageExporter:
    """Exports crawl and scrape results to multiple structured formats."""

    @staticmethod
    def to_json(
        results: list[CrawlResult],
        metadata: dict[str, Any] | None = None,
        indent: int = 2,
    ) -> str:
        """Export results to formatted JSON with metadata envelope."""
        envelope = {
            "metadata": metadata or {},
            "total_pages": len(results),
            "data": [r.model_dump(mode="json") for r in results],
        }
        return json.dumps(envelope, indent=indent, default=str)

    @staticmethod
    def to_jsonl(results: list[CrawlResult]) -> str:
        """Export results as newline-delimited JSON."""
        lines = [json.dumps(r.model_dump(mode="json"), default=str) for r in results]
        return "\n".join(lines)

    @staticmethod
    def to_csv(results: list[CrawlResult]) -> str:
        """Export summary table of crawled pages as CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "URL",
                "Final URL",
                "Status Code",
                "Title",
                "Markdown Size (bytes)",
                "Internal Links",
                "External Links",
                "Strategy",
                "Duration (s)",
                "Confidence",
            ]
        )
        for r in results:
            writer.writerow(
                [
                    r.url,
                    r.final_url,
                    r.status_code,
                    r.title or "",
                    r.cleaned_markdown_size,
                    len(r.internal_links),
                    len(r.external_links),
                    r.strategy_used.value,
                    f"{r.elapsed_seconds:.2f}",
                    r.confidence,
                ]
            )
        return output.getvalue()

    @staticmethod
    def to_markdown(results: list[CrawlResult], title: str = "Crawl Report") -> str:
        """Export crawl results into a consolidated Markdown document."""
        if len(results) == 1:
            r = results[0]
            header = f"# {r.title or r.final_url}\n\n"
            meta = (
                f"- **Source URL:** {r.final_url}\n"
                f"- **Status Code:** {r.status_code}\n"
                f"- **Strategy:** {r.strategy_used.value}\n"
                f"- **Crawled At:** {r.crawled_at}\n\n---\n\n"
            )
            return header + meta + (r.markdown or "(No content extracted)")

        md_lines = [
            f"# {title}",
            "",
            f"**Total Pages Crawled:** {len(results)}",
            "",
            "---",
            "",
        ]

        for idx, r in enumerate(results, 1):
            md_lines.extend(
                [
                    f"## {idx}. {r.title or r.url}",
                    f"- **URL:** {r.final_url}",
                    f"- **Status Code:** {r.status_code}",
                    f"- **Strategy:** {r.strategy_used.value}",
                    f"- **Confidence:** {r.confidence}",
                    "",
                    "### Content",
                    r.markdown or "(No content extracted)",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(md_lines)

    @staticmethod
    def to_text(results: list[CrawlResult], title: str = "Web Scraping & Crawl Report") -> str:
        """Export crawl results to formatted plain text (.txt)."""
        if len(results) == 1:
            r = results[0]
            lines = [
                "=" * 78,
                (r.title or "Untitled Page").center(78),
                "=" * 78,
                f"URL:     {r.final_url}",
                f"Status:  {r.status_code} | Strategy: {r.strategy_used.value} | Confidence: {r.confidence}",
                f"Links:   {len(r.internal_links)} internal, {len(r.external_links)} external",
                "-" * 78,
                "",
                r.markdown.strip() if r.markdown else "(No content extracted)",
                "",
                "=" * 78,
            ]
            return "\n".join(lines)

        lines = [
            "=" * 78,
            title.upper().center(78),
            "=" * 78,
            f"Total Pages: {len(results)}",
            "-" * 78,
            "",
        ]

        for idx, r in enumerate(results, 1):
            lines.extend(
                [
                    f"[{idx}] {r.title or 'Untitled Page'}",
                    f"URL:        {r.final_url}",
                    f"Status:     {r.status_code} | Strategy: {r.strategy_used.value} | Confidence: {r.confidence}",
                    f"Links:      {len(r.internal_links)} internal, {len(r.external_links)} external",
                    "-" * 50,
                    "CONTENT:",
                    r.markdown.strip() if r.markdown else "(No content extracted)",
                    "",
                    "=" * 78,
                    "",
                ]
            )

        return "\n".join(lines)

    @staticmethod
    def to_pdf(
        results: list[CrawlResult],
        target_path_or_buf: str | Path | io.BytesIO,
        title: str = "Web Scraping & Crawling Report",
    ) -> bytes:
        """Export crawl results into a professionally formatted PDF document."""
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError(
                "ReportLab is required for PDF export. Install with 'pip install reportlab'"
            )

        if isinstance(target_path_or_buf, (str, Path)):
            buf = io.BytesIO()
            save_to_file = True
            out_file_path = Path(target_path_or_buf)
        else:
            buf = target_path_or_buf
            save_to_file = False
            out_file_path = None

        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()

        # Custom paragraph styles
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            alignment=0,
            spaceAfter=10,
        )

        h2_style = ParagraphStyle(
            "PageHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0284c7"),
            spaceBefore=12,
            spaceAfter=6,
        )

        body_style = ParagraphStyle(
            "BodyTextCustom",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
            spaceAfter=6,
        )

        meta_label_style = ParagraphStyle(
            "MetaLabel",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        )

        meta_val_style = ParagraphStyle(
            "MetaVal",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#0f172a"),
        )

        story = []

        # Document Header
        story.append(Paragraph(title, title_style))
        story.append(
            Paragraph(
                f"Generated by Ethical AI Web Crawler &bull; Total Pages: {len(results)}",
                body_style,
            )
        )
        story.append(Spacer(1, 8))
        story.append(
            HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=15)
        )

        for idx, r in enumerate(results, 1):
            if idx > 1:
                story.append(PageBreak())

            # Page Title
            page_title = f"{idx}. {r.title or 'Untitled Page'}"
            # Escape HTML characters for ReportLab Paragraph
            safe_title = page_title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe_title, h2_style))

            # Metadata Table
            safe_url = r.final_url.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            meta_data = [
                [
                    Paragraph("URL", meta_label_style),
                    Paragraph(f'<font color="#0284c7">{safe_url}</font>', meta_val_style),
                ],
                [
                    Paragraph("Status", meta_label_style),
                    Paragraph(
                        f"{r.status_code} | Strategy: {r.strategy_used.value} | Confidence: {r.confidence}",
                        meta_val_style,
                    ),
                ],
                [
                    Paragraph("Stats", meta_label_style),
                    Paragraph(
                        f"Size: {r.cleaned_markdown_size:,} bytes | Elapsed: {r.elapsed_seconds:.2f}s | Links: {len(r.internal_links)} internal, {len(r.external_links)} external",
                        meta_val_style,
                    ),
                ],
            ]

            t = Table(meta_data, colWidths=[60, 460])
            t.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.append(t)
            story.append(Spacer(1, 10))

            # Content Section
            story.append(
                Paragraph(
                    "<b>Extracted Content:</b>",
                    ParagraphStyle("SubHead", parent=body_style, fontName="Helvetica-Bold"),
                )
            )
            story.append(Spacer(1, 4))

            # Convert markdown content into formatted paragraphs
            clean_text = r.markdown.strip() if r.markdown else "(No content extracted)"
            paragraphs = clean_text.split("\n\n")
            # Allow up to 100 paragraphs for single page scrape, 40 for multi-page crawl
            max_para = 100 if len(results) == 1 else 40
            for p in paragraphs[:max_para]:
                p_text = p.strip()
                if not p_text:
                    continue

                # Strip markdown links to plain text
                p_text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", p_text)
                # Escape XML entities for ReportLab
                safe_p = p_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

                # Handle headings
                if safe_p.startswith("#"):
                    level = len(safe_p) - len(safe_p.lstrip("#"))
                    heading_text = safe_p.lstrip("#").strip()
                    h_size = max(10, 14 - level)
                    story.append(
                        Paragraph(
                            f"<b>{heading_text}</b>",
                            ParagraphStyle(
                                "H", parent=body_style, fontSize=h_size, leading=h_size + 3
                            ),
                        )
                    )
                else:
                    story.append(Paragraph(safe_p, body_style))

                story.append(Spacer(1, 3))

            story.append(Spacer(1, 10))
            story.append(
                HRFlowable(
                    width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0"), spaceAfter=10
                )
            )

        doc.build(story)
        pdf_bytes = buf.getvalue()

        if save_to_file and out_file_path:
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            out_file_path.write_bytes(pdf_bytes)

        return pdf_bytes

    @staticmethod
    def save_to_sqlite(results: list[CrawlResult], db_path: str | Path) -> None:
        """Save results into a local SQLite database."""
        conn = sqlite3.connect(str(db_path))
        with conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS pages (
                    url TEXT PRIMARY KEY,
                    final_url TEXT,
                    status_code INTEGER,
                    title TEXT,
                    markdown TEXT,
                    metadata_json TEXT,
                    internal_links_count INTEGER,
                    external_links_count INTEGER,
                    strategy TEXT,
                    confidence TEXT,
                    crawled_at TEXT
                )
                """
            )
            for r in results:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO pages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        r.url,
                        r.final_url,
                        r.status_code,
                        r.title,
                        r.markdown,
                        json.dumps(r.metadata.model_dump(mode="json")),
                        len(r.internal_links),
                        len(r.external_links),
                        r.strategy_used.value,
                        r.confidence,
                        str(r.crawled_at),
                    ),
                )
        conn.close()

    @classmethod
    def save_file(
        cls,
        results: list[CrawlResult],
        target_path: str | Path,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Save results to file detecting format by file extension (.json, .jsonl, .csv, .md, .txt, .pdf, .sqlite)."""
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        ext = path.suffix.lower()

        if ext == ".json":
            content = cls.to_json(results, metadata)
            path.write_text(content, encoding="utf-8")
        elif ext == ".jsonl":
            content = cls.to_jsonl(results)
            path.write_text(content, encoding="utf-8")
        elif ext == ".csv":
            content = cls.to_csv(results)
            path.write_text(content, encoding="utf-8")
        elif ext in (".md", ".markdown"):
            content = cls.to_markdown(results)
            path.write_text(content, encoding="utf-8")
        elif ext in (".txt", ".text"):
            content = cls.to_text(results)
            path.write_text(content, encoding="utf-8")
        elif ext == ".pdf":
            cls.to_pdf(results, path)
        elif ext in (".db", ".sqlite", ".sqlite3"):
            cls.save_to_sqlite(results, path)
        else:
            # Default to json
            content = cls.to_json(results, metadata)
            path.write_text(content, encoding="utf-8")

        return str(path.resolve())

    @classmethod
    def export_bytes(
        cls,
        results: list[CrawlResult],
        fmt: str = "json",
        metadata: dict[str, Any] | None = None,
    ) -> tuple[bytes, str, str]:
        """Export results into raw bytes with appropriate MIME type and filename.

        Returns (file_bytes, media_type, filename).
        """
        fmt = fmt.lower().strip(".")
        if fmt == "pdf":
            pdf_bytes = cls.to_pdf(results, io.BytesIO())
            return pdf_bytes, "application/pdf", "crawl_results.pdf"
        elif fmt in ("md", "markdown"):
            md_text = cls.to_markdown(results)
            return md_text.encode("utf-8"), "text/markdown; charset=utf-8", "crawl_results.md"
        elif fmt in ("txt", "text"):
            plain = cls.to_text(results)
            return plain.encode("utf-8"), "text/plain; charset=utf-8", "crawl_results.txt"
        elif fmt == "csv":
            csv_text = cls.to_csv(results)
            return csv_text.encode("utf-8"), "text/csv; charset=utf-8", "crawl_results.csv"
        elif fmt == "jsonl":
            jsonl_text = cls.to_jsonl(results)
            return (
                jsonl_text.encode("utf-8"),
                "application/x-ndjson; charset=utf-8",
                "crawl_results.jsonl",
            )
        else:  # json
            json_text = cls.to_json(results, metadata)
            return (
                json_text.encode("utf-8"),
                "application/json; charset=utf-8",
                "crawl_results.json",
            )
