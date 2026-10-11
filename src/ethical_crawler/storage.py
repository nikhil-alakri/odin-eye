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
    def _pdf_escape(text: str) -> str:
        cleaned = (
            text.replace("\u20b9", "Rs.")
            .replace("\u2014", " - ")
            .replace("\u2013", "-")
            .replace("\u2011", "-")
            .replace("\u2018", "'")
            .replace("\u2019", "'")
            .replace("\u201c", '"')
            .replace("\u201d", '"')
            .replace("\u2026", "...")
            .replace("\u00a0", " ")
        )
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", cleaned)
        cleaned = re.sub(r"\]\([^)]*\)", "", cleaned)
        cleaned = cleaned.encode("latin-1", "replace").decode("latin-1")
        return (
            cleaned.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _md_inline(text: str) -> str:
        """Turn a small markdown subset into ReportLab markup."""
        safe = StorageExporter._pdf_escape(text.strip())
        safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
        safe = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"<i>\1</i>", safe)
        safe = re.sub(r"`(.+?)`", r'<font face="Courier">\1</font>', safe)
        return safe

    @classmethod
    def to_dossier_pdf(
        cls,
        markdown: str,
        title: str,
        target_path_or_buf: str | Path | io.BytesIO,
    ) -> bytes:
        """Render a website intelligence report as a readable, sectioned PDF."""
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

        ink = colors.HexColor("#1c1b1b")
        muted = colors.HexColor("#444932")
        olive = colors.HexColor("#536600")
        lime = colors.HexColor("#d4ff00")
        teal = colors.HexColor("#00677f")
        line = colors.HexColor("#e5e2e1")
        wash = colors.HexColor("#f6f3f2")
        card = colors.HexColor("#fafafa")

        page_width, page_height = letter
        margin = 42

        def _draw_page(canvas, doc):
            canvas.saveState()
            canvas.setFillColor(lime)
            canvas.rect(0, page_height - 8, page_width, 8, fill=1, stroke=0)
            canvas.setFillColor(ink)
            canvas.setFont("Helvetica-Bold", 8)
            canvas.drawString(margin, page_height - 24, "CRAWL // ETHIC")
            canvas.setFillColor(muted)
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(page_width - margin, page_height - 24, "Website Intelligence Report")
            canvas.setStrokeColor(line)
            canvas.setLineWidth(0.6)
            canvas.line(margin, 32, page_width - margin, 32)
            canvas.setFillColor(muted)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(margin, 18, "Generated from crawled knowledge")
            canvas.drawRightString(page_width - margin, 18, f"Page {doc.page}")
            canvas.restoreState()

        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            rightMargin=margin,
            leftMargin=margin,
            topMargin=42,
            bottomMargin=46,
        )
        content_width = page_width - (margin * 2)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DossierTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor=ink,
            alignment=0,
            spaceAfter=4,
        )
        meta_style = ParagraphStyle(
            "DossierMeta",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=muted,
            spaceAfter=8,
        )
        h2_style = ParagraphStyle(
            "DossierH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=olive,
            spaceBefore=12,
            spaceAfter=6,
        )
        h3_style = ParagraphStyle(
            "DossierH3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=ink,
            spaceBefore=2,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "DossierBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=ink,
            spaceAfter=3,
        )
        bullet_style = ParagraphStyle(
            "DossierBullet",
            parent=body_style,
            leftIndent=12,
            bulletIndent=0,
            spaceAfter=2,
        )
        quote_style = ParagraphStyle(
            "DossierQuote",
            parent=body_style,
            textColor=teal,
            leftIndent=8,
            borderPadding=4,
        )
        cell_style = ParagraphStyle(
            "DossierCell",
            parent=body_style,
            fontSize=8,
            leading=11,
            spaceAfter=0,
        )
        head_cell = ParagraphStyle(
            "DossierHeadCell",
            parent=cell_style,
            fontName="Helvetica-Bold",
            textColor=ink,
        )

        story: list[Any] = []
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="72", thickness=4, color=lime, spaceAfter=8))
        display_title = title
        lines = [ln.rstrip() for ln in (markdown or "").splitlines()]
        if lines and lines[0].startswith("# "):
            display_title = lines[0][2:].strip() or title
            lines = lines[1:]
        story.append(Paragraph(cls._md_inline(display_title), title_style))
        story.append(
            Paragraph("Readable briefing built from stored crawl pages.", meta_style)
        )

        def flush_table(rows: list[list[str]]) -> None:
            if not rows:
                return
            header = rows[0]
            body_rows = [row for row in rows[1:] if not all(set(c) <= set(":- ") for c in row)]
            col_count = max(len(header), max((len(r) for r in body_rows), default=0))
            if col_count == 0:
                return
            col_w = content_width / col_count
            data = []
            data.append(
                [Paragraph(cls._md_inline(cell or ""), head_cell) for cell in header[:col_count]]
            )
            for row in body_rows:
                padded = row + [""] * (col_count - len(row))
                data.append(
                    [Paragraph(cls._md_inline(cell or ""), cell_style) for cell in padded[:col_count]]
                )
            table = Table(data, colWidths=[col_w] * col_count, repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), lime),
                        ("TEXTCOLOR", (0, 0), (-1, 0), ink),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, wash]),
                        ("GRID", (0, 0), (-1, -1), 0.4, line),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            story.append(Spacer(1, 4))
            story.append(table)
            story.append(Spacer(1, 8))

        table_rows: list[list[str]] = []
        card_open = False

        def close_card() -> None:
            nonlocal card_open
            card_open = False

        i = 0
        while i < len(lines):
            raw = lines[i].strip()
            indent = len(lines[i]) - len(lines[i].lstrip(" "))
            if raw.startswith("|") and raw.endswith("|"):
                cells = [c.strip() for c in raw.strip("|").split("|")]
                table_rows.append(cells)
                i += 1
                continue
            if table_rows:
                flush_table(table_rows)
                table_rows = []

            if not raw:
                i += 1
                continue
            if raw.startswith("## "):
                close_card()
                story.append(Paragraph(cls._md_inline(raw[3:]), h2_style))
                story.append(HRFlowable(width="100%", thickness=1, color=lime, spaceAfter=6))
            elif raw.startswith("### "):
                close_card()
                card_open = True
                banner = Table(
                    [[Paragraph(cls._md_inline(raw[4:]), h3_style)]],
                    colWidths=[content_width],
                )
                banner.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, -1), wash),
                            ("BOX", (0, 0), (-1, -1), 0.6, line),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                            ("LINEBEFORE", (0, 0), (0, -1), 4, olive),
                        ]
                    )
                )
                story.append(Spacer(1, 6))
                story.append(banner)
            elif raw.startswith(">"):
                story.append(Paragraph(cls._md_inline(raw.lstrip("> ").strip()), quote_style))
            elif raw.startswith(("- ", "* ")):
                bullet = bullet_style
                if indent >= 2:
                    bullet = ParagraphStyle(
                        "DossierBulletNested",
                        parent=bullet_style,
                        leftIndent=26,
                        textColor=muted,
                    )
                story.append(Paragraph(cls._md_inline(raw[2:]), bullet, bulletText="-"))
            elif re.match(r"^\d+\.\s", raw):
                story.append(Paragraph(cls._md_inline(raw), bullet_style))
            else:
                style = body_style
                if card_open and raw.startswith("*") and raw.endswith("*"):
                    style = meta_style
                story.append(Paragraph(cls._md_inline(raw), style))
            i += 1

        if table_rows:
            flush_table(table_rows)

        doc.build(story, onFirstPage=_draw_page, onLaterPages=_draw_page)
        pdf_bytes = buf.getvalue()
        if save_to_file and out_file_path:
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            out_file_path.write_bytes(pdf_bytes)
        return pdf_bytes

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

            clean_text = r.markdown.strip() if r.markdown else "(No content extracted)"
            # Line-oriented so markdown tables and long reports are not dropped
            # after a small paragraph cap, and one bad line cannot fail the PDF.
            raw_lines = clean_text.splitlines()
            max_lines = 800 if len(results) == 1 else 240
            for raw_line in raw_lines[:max_lines]:
                p_text = raw_line.strip()
                if not p_text:
                    story.append(Spacer(1, 4))
                    continue
                p_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", p_text)
                p_text = p_text.encode("latin-1", "replace").decode("latin-1")
                safe_p = (
                    p_text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                try:
                    if safe_p.startswith("#"):
                        level = len(safe_p) - len(safe_p.lstrip("#"))
                        heading_text = safe_p.lstrip("#").strip() or "Section"
                        h_size = max(10, 14 - min(level, 4))
                        story.append(
                            Paragraph(
                                f"<b>{heading_text}</b>",
                                ParagraphStyle(
                                    f"H{level}",
                                    parent=body_style,
                                    fontSize=h_size,
                                    leading=h_size + 3,
                                    spaceBefore=6,
                                ),
                            )
                        )
                    else:
                        story.append(Paragraph(safe_p, body_style))
                except Exception:
                    plain = safe_p.replace("<", "").replace(">", "")[:500]
                    story.append(Paragraph(plain or "(line skipped)", body_style))
                story.append(Spacer(1, 2))

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
            is_dossier = bool(metadata and metadata.get("dossier"))
            if is_dossier and results:
                pdf_bytes = cls.to_dossier_pdf(
                    results[0].markdown or "",
                    results[0].title or "Website Intelligence Report",
                    io.BytesIO(),
                )
            else:
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
