"""ChromaDB Vector Store for persistent crawling history, semantic search, and caching.

Adheres strictly to the Database Preservation Rule:
All vector operations are non-destructive (upsert-only).
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import chromadb
from chromadb.config import Settings as ChromaSettings

from ethical_crawler.config import get_settings
from ethical_crawler.types import CrawlResult, CrawlStrategy, PageMetadata

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages local ChromaDB vector database for ethical crawler storage & retrieval."""

    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str | None = None,
    ):
        settings = get_settings()
        self.persist_dir = Path(persist_dir or settings.chroma_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or settings.chroma_collection

        # Initialize persistent ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir.resolve()),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine", "description": "Crawled web pages and AI knowledge"},
        )

    def _normalize_id(self, url: str) -> str:
        """Create consistent identifier from URL."""
        return url.strip().rstrip("/")

    def upsert_page(
        self,
        result: CrawlResult,
        ai_data: dict[str, Any] | None = None,
    ) -> None:
        """Non-destructively upsert crawled page into ChromaDB vector store with revision tracking."""
        if not result.markdown and not result.title:
            return

        doc_id = self._normalize_id(result.final_url or result.url)
        content = result.markdown.strip() if result.markdown else (result.title or "")

        # Extract domain for filtering
        parsed = urlparse(result.final_url or result.url)
        domain = parsed.netloc.lower()

        # Check existing record for revision & growth tracking
        revision_count = 1
        growth_delta_bytes = 0
        first_crawled_at = result.crawled_at.isoformat()
        is_updated = False

        try:
            existing = self.collection.get(ids=[doc_id], include=["metadatas"])
            if existing and existing["ids"] and existing["metadatas"]:
                old_meta = existing["metadatas"][0]
                old_size = int(old_meta.get("cleaned_markdown_size", 0))
                new_size = int(result.cleaned_markdown_size)
                growth_delta_bytes = new_size - old_size
                revision_count = int(old_meta.get("revision_count", 1)) + 1
                first_crawled_at = old_meta.get(
                    "first_crawled_at", old_meta.get("crawled_at", first_crawled_at)
                )
                is_updated = bool(old_size != new_size or growth_delta_bytes != 0)
                # If existing record had AI data and none passed in this update, preserve old AI data
                if (
                    not ai_data
                    and old_meta.get("ai_data_json")
                    and old_meta["ai_data_json"] != "{}"
                ):
                    try:
                        ai_data = json.loads(old_meta["ai_data_json"])
                    except Exception:
                        pass
        except Exception as check_err:
            logger.debug("Could not inspect existing record for revisions: %s", check_err)

        metadata: dict[str, Any] = {
            "url": result.url,
            "final_url": result.final_url,
            "domain": domain,
            "title": result.title or "Untitled Page",
            "status_code": int(result.status_code),
            "strategy": result.strategy_used.value,
            "cleaned_markdown_size": int(result.cleaned_markdown_size),
            "crawled_at": result.crawled_at.isoformat(),
            "first_crawled_at": first_crawled_at,
            "revision_count": revision_count,
            "growth_delta_bytes": growth_delta_bytes,
            "is_updated": is_updated,
            "confidence": result.confidence,
            "internal_links_count": len(result.internal_links),
            "external_links_count": len(result.external_links),
            "internal_links_json": json.dumps(result.internal_links[:200]),
            "ai_data_json": json.dumps(ai_data or {}),
            "ai_model_used": result.ai_model_used or "",
            "metadata_json": json.dumps(result.metadata.model_dump(mode="json")),
        }

        # Safe non-destructive upsert
        self.collection.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata],
        )
        logger.info(
            "Saved page to vector store: %s (rev: %d, delta: %+d B)",
            doc_id,
            revision_count,
            growth_delta_bytes,
        )

    def get_cached_page(
        self,
        url: str,
        max_age_days: int | None = None,
    ) -> tuple[CrawlResult, dict[str, Any] | None] | None:
        """Check if URL exists in vector cache and is fresh.

        Returns (CrawlResult, ai_data) if found and fresh, else None.
        """
        settings = get_settings()
        ttl_days = max_age_days if max_age_days is not None else settings.cache_ttl_days
        doc_id = self._normalize_id(url)

        try:
            records = self.collection.get(
                ids=[doc_id],
                include=["documents", "metadatas"],
            )
        except Exception as exc:
            logger.warning("Cache lookup error for %s: %s", url, exc)
            return None

        if not records or not records["ids"]:
            return None

        metadata = records["metadatas"][0]
        document = records["documents"][0]

        # Do not serve empty or 0-byte cached records; trigger a fresh fetch
        if (
            not document
            or len(document.strip()) == 0
            or int(metadata.get("cleaned_markdown_size", 0)) == 0
        ):
            logger.debug("Cache entry for %s has empty content, skipping cache hit", url)
            return None

        # Verify freshness
        crawled_at_str = metadata.get("crawled_at")
        if crawled_at_str:
            try:
                crawled_at = datetime.fromisoformat(crawled_at_str)
                age = datetime.utcnow() - crawled_at
                if age > timedelta(days=ttl_days):
                    logger.debug("Cache expired for %s (age: %s days)", url, age.days)
                    return None
            except Exception:
                pass
        else:
            crawled_at = datetime.utcnow()

        # Reconstruct CrawlResult
        try:
            raw_meta = json.loads(metadata.get("metadata_json", "{}"))
            page_meta = PageMetadata(**raw_meta)
        except Exception:
            page_meta = PageMetadata(title=metadata.get("title"))

        ai_data = None
        if metadata.get("ai_data_json"):
            try:
                ai_data = json.loads(metadata["ai_data_json"])
            except Exception:
                ai_data = None

        internal_links = []
        if metadata.get("internal_links_json"):
            try:
                internal_links = json.loads(metadata["internal_links_json"])
            except Exception:
                internal_links = []

        result = CrawlResult(
            url=metadata.get("url", url),
            final_url=metadata.get("final_url", url),
            status_code=int(metadata.get("status_code", 200)),
            title=metadata.get("title"),
            markdown=document,
            raw_html=None,
            metadata=page_meta,
            internal_links=internal_links,
            external_links=[],
            cleaned_markdown_size=int(metadata.get("cleaned_markdown_size", len(document))),
            strategy_used=CrawlStrategy(metadata.get("strategy", "http")),
            elapsed_seconds=0.01,  # Cache hit is near instantaneous
            depth=0,
            confidence=metadata.get("confidence", "HIGH"),
            crawled_at=crawled_at,
            ai_data=ai_data,
            ai_model_used=metadata.get("ai_model_used") or None,
        )

        return result, ai_data

    def semantic_search(
        self,
        query: str,
        n_results: int = 5,
        domain: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search crawled pages by meaning using vector embeddings."""
        if not query.strip():
            return []

        where_filter = None
        if domain:
            where_filter = {"domain": domain.lower().strip()}

        count = self.collection.count()
        if count == 0:
            return []

        actual_n = min(n_results, count)

        try:
            query_kwargs: dict[str, Any] = {
                "query_texts": [query],
                "n_results": actual_n,
                "include": ["documents", "metadatas", "distances"],
            }
            if where_filter:
                query_kwargs["where"] = where_filter

            res = self.collection.query(**query_kwargs)
        except Exception as exc:
            logger.error("Semantic search error: %s", exc)
            return []

        matches = []
        if res and res["ids"] and len(res["ids"][0]) > 0:
            for i in range(len(res["ids"][0])):
                doc_id = res["ids"][0][i]
                meta = res["metadatas"][0][i] if res["metadatas"] else {}
                doc = res["documents"][0][i] if res["documents"] else ""
                distance = res["distances"][0][i] if res["distances"] else 1.0

                # Compute similarity score from cosine distance (0=identical, 2=opposite)
                similarity = max(0.0, round(1.0 - (distance / 2.0), 3))

                # Create preview snippet
                snippet = doc[:300] + ("..." if len(doc) > 300 else "")

                matches.append(
                    {
                        "id": doc_id,
                        "url": meta.get("url", doc_id),
                        "final_url": meta.get("final_url", doc_id),
                        "title": meta.get("title", "Untitled Page"),
                        "snippet": snippet,
                        "similarity": similarity,
                        "crawled_at": meta.get("crawled_at"),
                        "size": meta.get("cleaned_markdown_size", len(doc)),
                    }
                )

        return matches

    def list_stored_pages(self, limit: int = 100) -> list[dict[str, Any]]:
        """List summary of all crawled pages stored in the vector database."""
        count = self.collection.count()
        if count == 0:
            return []

        try:
            records = self.collection.get(
                limit=limit,
                include=["metadatas"],
            )
        except Exception as exc:
            logger.error("Error listing pages: %s", exc)
            return []

        pages = []
        if records and records["ids"]:
            for i in range(len(records["ids"])):
                doc_id = records["ids"][i]
                meta = records["metadatas"][i] if records["metadatas"] else {}
                pages.append(
                    {
                        "id": doc_id,
                        "url": meta.get("url", doc_id),
                        "final_url": meta.get("final_url", doc_id),
                        "domain": meta.get("domain", ""),
                        "title": meta.get("title", "Untitled Page"),
                        "status_code": meta.get("status_code", 200),
                        "size": meta.get("cleaned_markdown_size", 0),
                        "strategy": meta.get("strategy", "http"),
                        "crawled_at": meta.get("crawled_at"),
                        "first_crawled_at": meta.get("first_crawled_at"),
                        "revision_count": int(meta.get("revision_count", 1)),
                        "growth_delta_bytes": int(meta.get("growth_delta_bytes", 0)),
                        "is_updated": bool(meta.get("is_updated", False)),
                        "has_ai": bool(
                            meta.get("ai_data_json") and meta.get("ai_data_json") != "{}"
                        ),
                    }
                )

        # Sort newest first
        pages.sort(key=lambda x: str(x.get("crawled_at", "")), reverse=True)
        return pages

    def delete_page(self, url: str) -> bool:
        """Safely delete a single crawled page from ChromaDB by URL."""
        doc_id = self._normalize_id(url)
        try:
            rec = self.collection.get(ids=[doc_id])
            if not rec or not rec["ids"]:
                return False
            self.collection.delete(ids=[doc_id])
            logger.info("Deleted page from vector store: %s", doc_id)
            return True
        except Exception as exc:
            logger.error("Error deleting page %s: %s", url, exc)
            return False

    def delete_domain(self, domain: str) -> int:
        """Safely delete all crawled pages belonging to a specific domain."""
        target_domain = domain.lower().strip()
        try:
            records = self.collection.get(
                where={"domain": target_domain},
                include=["metadatas"],
            )
            if not records or not records["ids"]:
                return 0
            ids_to_delete = records["ids"]
            self.collection.delete(ids=ids_to_delete)
            logger.info("Deleted %d pages for domain %s", len(ids_to_delete), target_domain)
            return len(ids_to_delete)
        except Exception as exc:
            logger.error("Error deleting domain %s: %s", domain, exc)
            return 0

    def list_domains_summary(self, limit: int = 200) -> list[dict[str, Any]]:
        """Group stored pages by domain with aggregated statistics."""
        pages = self.list_stored_pages(limit=limit)
        domains_map: dict[str, dict[str, Any]] = {}

        for p in pages:
            dom = p.get("domain") or "unknown"
            if dom not in domains_map:
                domains_map[dom] = {
                    "domain": dom,
                    "page_count": 0,
                    "total_pages": 0,
                    "total_size": 0,
                    "last_crawled": p.get("crawled_at"),
                    "newest_crawled_at": p.get("crawled_at"),
                    "ai_profiles_count": 0,
                    "ai_profile_count": 0,
                    "pages": [],
                }
            d_entry = domains_map[dom]
            d_entry["page_count"] += 1
            d_entry["total_pages"] += 1
            d_entry["total_size"] += int(p.get("size", 0))
            if p.get("has_ai"):
                d_entry["ai_profiles_count"] += 1
                d_entry["ai_profile_count"] += 1
            if str(p.get("crawled_at", "")) > str(d_entry["last_crawled"] or ""):
                d_entry["last_crawled"] = p.get("crawled_at")
                d_entry["newest_crawled_at"] = p.get("crawled_at")
            d_entry["pages"].append(p)

        summary = list(domains_map.values())
        summary.sort(key=lambda x: (x["total_pages"], x["total_size"]), reverse=True)
        return summary

    def get_store_overview(self, limit: int = 300) -> dict[str, Any]:
        """Return collection health, field mappings, and domain → document IDs."""
        pages = self.list_stored_pages(limit=limit)
        domains = self.list_domains_summary(limit=limit)
        coll_meta = self.collection.metadata or {}
        field_mappings = [
            {
                "field": "id",
                "source": "Normalized URL (strip, no trailing slash)",
                "role": "Primary key / Chroma document ID",
            },
            {"field": "url", "source": "CrawlResult.url", "role": "Requested seed URL"},
            {
                "field": "final_url",
                "source": "CrawlResult.final_url",
                "role": "Canonical URL after redirects",
            },
            {"field": "domain", "source": "urlparse(final_url).netloc", "role": "Grouping key"},
            {"field": "title", "source": "Page <title> / metadata", "role": "Display label"},
            {
                "field": "document",
                "source": "Cleaned markdown",
                "role": "Embedded text used for cosine search",
            },
            {
                "field": "cleaned_markdown_size",
                "source": "len(markdown)",
                "role": "Byte size and growth tracking",
            },
            {
                "field": "revision_count",
                "source": "Incremented on upsert",
                "role": "How many times this URL was recrawled",
            },
            {
                "field": "growth_delta_bytes",
                "source": "new_size - previous_size",
                "role": "Content growth between revisions",
            },
            {
                "field": "ai_data_json",
                "source": "NVIDIA NIM extraction",
                "role": "Structured JSON overlay (company/product/FAQ)",
            },
            {
                "field": "ai_model_used",
                "source": "Extractor model id",
                "role": "Which model produced ai_data",
            },
            {
                "field": "internal_links_json",
                "source": "Link extractor",
                "role": "Outbound internal URLs (capped)",
            },
            {"field": "strategy", "source": "http | browser | auto", "role": "Fetch engine used"},
            {"field": "crawled_at", "source": "ISO timestamp", "role": "Latest crawl time"},
            {
                "field": "first_crawled_at",
                "source": "ISO timestamp",
                "role": "First time this URL entered the store",
            },
        ]
        return {
            "status": "active",
            "engine": "ChromaDB",
            "persist_dir": str(self.persist_dir.resolve()),
            "collection": self.collection_name,
            "distance_space": coll_meta.get("hnsw:space", "cosine"),
            "description": coll_meta.get("description", ""),
            "document_count": self.collection.count(),
            "listed_count": len(pages),
            "domain_count": len(domains),
            "field_mappings": field_mappings,
            "domains": [
                {
                    "domain": d.get("domain"),
                    "page_count": d.get("total_pages", d.get("page_count", 0)),
                    "total_size": d.get("total_size", 0),
                    "ai_profiles": d.get("ai_profiles_count", 0),
                    "last_crawled": d.get("last_crawled"),
                }
                for d in domains
            ],
            "documents": pages,
        }

    def count_pages(self) -> int:
        """Return total unique crawled pages in database."""
        return self.collection.count()

    async def ask_crawled_knowledge(
        self,
        question: str,
        n_context: int = 3,
    ) -> dict[str, Any]:
        """Ask question answered by LLM using relevant crawled page chunks (RAG)."""
        settings = get_settings()
        from openai import AsyncOpenAI

        # 1. Semantic search for context
        matches = self.semantic_search(question, n_results=n_context)
        if not matches:
            return {
                "answer": "No relevant crawled pages found in database. Please crawl or scrape websites first.",
                "sources": [],
            }

        # 2. Build context
        context_blocks = []
        sources = []
        for idx, m in enumerate(matches, 1):
            context_blocks.append(
                f"[Source {idx}]: {m['title']} ({m['final_url']})\n{m['snippet']}\n"
            )
            sources.append({"title": m["title"], "url": m["final_url"]})

        context_str = "\n---\n".join(context_blocks)

        prompt = (
            f"You are an AI assistant answering questions using information from crawled web pages.\n\n"
            f"Context from crawled websites:\n{context_str}\n\n"
            f"User Question: {question}\n\n"
            f"Provide a clear, accurate, and concise answer strictly based on the context above. "
            f"Cite the relevant source URLs where applicable."
        )

        if not settings.ai_api_key:
            return {
                "answer": (
                    f"Found {len(matches)} relevant pages in the vector database, but AI API key is not configured.\n\n"
                    f"Top matching pages:\n"
                    + "\n".join(f"- {s['title']}: {s['url']}" for s in sources)
                ),
                "sources": sources,
            }

        client = AsyncOpenAI(
            base_url=settings.ai_base_url,
            api_key=settings.ai_api_key,
        )

        try:
            resp = await client.chat.completions.create(
                model=settings.ai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=600,
            )
            answer = resp.choices[0].message.content or "No answer generated."
        except Exception as exc:
            answer = f"AI Generation failed: {exc}\n\nFound matching sources:\n" + "\n".join(
                f"- {s['title']}: {s['url']}" for s in sources
            )

        return {
            "answer": answer,
            "sources": sources,
        }


# Singleton instance
_VECTOR_STORE_INSTANCE: VectorStoreManager | None = None


def get_vector_store() -> VectorStoreManager:
    """Retrieve or create the singleton VectorStoreManager instance."""
    global _VECTOR_STORE_INSTANCE
    if _VECTOR_STORE_INSTANCE is None:
        _VECTOR_STORE_INSTANCE = VectorStoreManager()
    return _VECTOR_STORE_INSTANCE
