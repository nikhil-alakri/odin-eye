# Architecture & Workflow Diagrams: Autonomous Features Suite
**Date & Time**: 09-Oct-2026 14:25

This document details the architectural workflows, data flows, and component interactions for all 4 features:
1. **Feature 1**: Scheduled Crawling, Content Diff & Change Alerts
2. **Feature 2**: Vision & Multimodal Extraction (Screenshots, Vision LLM, PDF Ingestion)
3. **Feature 3**: Interactive Point-and-Click Visual Element Picker
4. **Feature 5**: Competitive Intelligence & Technology Stack Profiling

---

## 1. Feature 1: Scheduled Crawling, Content Diff & Change Alerts

### System Flowchart
```mermaid
flowchart TD
    subgraph UI["Dashboard & API Layer"]
        User["User / Dashboard UI"] -->|"Configure URL, Cadence, Webhook"| SchedModal["Schedules Modal & API"]
        SchedModal -->|"POST /v1/schedules"| SchedMgr["ScheduleManager"]
    end

    subgraph Scheduler["Background Scheduler Engine"]
        SchedMgr -->|"Persist Config"| SchedFile[("data/schedules.json")]
        Ticker["Async 15s Ticker Loop"] -->|"Check due jobs"| SchedMgr
        SchedMgr -->|"Trigger Job"| CrawlTask["Execute Crawl / Scrape Task"]
    end

    subgraph DiffAndAlert["Diff & Alert Processing"]
        CrawlTask -->|"Fetch Live Page"| LiveDoc["Current Live Markdown"]
        CrawlTask -->|"Fetch Baseline Record"| ChromaDB[("ChromaDB Vector Store")]
        LiveDoc --> DiffEngine["ContentDiffEngine"]
        ChromaDB --> DiffEngine

        DiffEngine -->|"Filter noise (CSRF, Timestamps)"| Cleaned["Normalized Text Comparison"]
        Cleaned -->|"difflib.SequenceMatcher"| RatioCalc{"Similarity Ratio < Threshold?"}

        RatioCalc -->|"No Change"| MarkClean["Status: Unchanged"]
        RatioCalc -->|"Changed"| GenDiff["Generate Syntax-Colored Unified Diff"]

        GenDiff -->|"Payload: diff summary, ratio, lines"| WebhookDisp["Webhook Alert Dispatcher"]
        WebhookDisp -->|"HTTP POST with Backoff"| SlackDiscord["Slack / Discord / Webhook Endpoints"]
    end

    subgraph Inspect["Inspection UI"]
        GenDiff -->|"Stored in Job Result"| DiffModal["Diff Inspector Modal (#diffModal)"]
    end
```

### Sequence Diagram: Scheduled Change Detection Cycle
```mermaid
sequenceDiagram
    autonumber
    participant Ticker as Background Ticker
    participant Mgr as ScheduleManager
    participant Crawl as EthicalCrawler
    participant Diff as ContentDiffEngine
    participant Alert as WebhookDispatcher
    participant Remote as Slack/Discord Webhook

    Ticker->>Mgr: tick() [Every 15s]
    Mgr->>Mgr: Identify due jobs (next_run_at <= now)
    Mgr->>Crawl: run_job(url, strategy)
    Crawl-->>Mgr: Live HTML & Markdown
    Mgr->>Diff: compare(previous_content, live_content)
    Diff->>Diff: Suppress dynamic noise & calculate ratio
    Diff-->>Mgr: ContentDiffResult (has_changed=True, similarity_ratio, html_diff)
    Mgr->>Mgr: Update data/schedules.json (last_diff, last_status="changed")
    alt Webhook URL Configured & Changed
        Mgr->>Alert: dispatch_alert(job, diff_result)
        Alert->>Remote: POST Webhook payload (Slack/Discord format)
        Remote-->>Alert: 200 OK
    end
```

---

## 2. Feature 2: Vision & Multimodal Extraction (Screenshots, Vision LLM, PDF Ingestion)

### Dual-Pipeline Flowchart
```mermaid
flowchart TD
    subgraph Ingestion["Input Requests"]
        ReqWeb["Web Page Scrape Request"]
        ReqPDF["PDF Document URL"]
    end

    subgraph PipelineA["Pipeline A: Headless Screenshot & Multimodal Vision"]
        ReqWeb -->|"enable_screenshot=True"| BrowserEng["Playwright Browser Engine"]
        BrowserEng -->|"page.screenshot(full_page=True)"| ImgFile[("data/screenshots/{domain}/{hash}_{ts}.jpg")]
        ImgFile -->|"GET /v1/screenshots/file"| PreviewUI["Dashboard Screenshot Viewer"]
        
        ImgFile -->|"User Prompt: chart_to_table / pricing_matrix"| VisionExt["VisionExtractor"]
        VisionExt -->|"Base64 Encoded JPEG + Prompt"| NIM["NVIDIA NIM Vision LLM (Llama 3.2 11B Vision)"]
        NIM -->|"Structured JSON / Markdown"| VisionCard["Preview Modal: Vision AI Card"]
    end

    subgraph PipelineB["Pipeline B: Streaming PDF Extractor"]
        ReqPDF -->|"POST /v1/pdf/parse"| StreamDownloader["HTTPX Streaming Client"]
        StreamDownloader -->|"Check Content-Length (<25MB)"| CapCheck{"Size <= 25MB?"}
        CapCheck -->|"Exceeds"| CapError["Reject with 413 Payload Too Large"]
        CapCheck -->|"Safe"| PyPDF["pypdf Reader"]
        PyPDF -->|"Extract text across pages"| TextExtract["Page Text Aggregator"]
        TextExtract -->|"Convert headings, bullets, tables"| PDFMarkdown["Clean Markdown Document"]
        PDFMarkdown -->|"index_in_chroma=True"| ChromaStore[("ChromaDB Vector Collection")]
    end
```

---

## 3. Feature 3: Interactive Point-and-Click Visual Element Picker

### Sandboxed DOM Architecture
```mermaid
flowchart TD
    subgraph Frontend["Dashboard UI"]
        ScraperForm["Scraper Form / RPA Builder"] -->|"Click 'Pick Element'"| PickerModal["Element Picker Modal (#elementPickerModal)"]
        PickerModal -->|"Set iframe src"| IframeSand["Sandboxed <iframe> (allow-scripts allow-same-origin)"]
    end

    subgraph API["FastAPI Sandbox Service"]
        IframeSand -->|"GET /v1/elements/sandbox?url=..."| SandboxEndpoint["get_element_picker_sandbox()"]
        SandboxEndpoint -->|"Fetch target webpage"| TargetWeb["Target Web Server"]
        TargetWeb -->>SandboxEndpoint["Raw HTML Response"]
        
        SandboxEndpoint --> Sanitize["ElementPicker.sanitize_and_prepare_html()"]
        
        subgraph Instrument["Instrumentation & Hardening Engine"]
            Sanitize --> Breakout["Neutralize window.top / parent.location breakouts"]
            Breakout --> BaseTag["Inject <base href='url'> for CSS & fonts"]
            BaseTag --> InjectJS["Inject Client Script: __ethic_element_picker_script__"]
        end
        
        InjectJS -->>IframeSand["Instrumented HTML (X-Frame-Options: SAMEORIGIN)"]
    end

    subgraph DOMInteraction["In-Iframe User Interaction"]
        UserMove["User hovers mouse"] --> Highlight["Outline element & show floating tag badge"]
        UserClick["User clicks element"] --> Intercept["e.preventDefault() & e.stopPropagation()"]
        Intercept --> GenerateSelector["Synthesize optimal CSS selector (#id, [data-*], .class)"]
        GenerateSelector --> PostMsg["window.parent.postMessage(ELEMENT_PICKED)"]
    end

    subgraph Feedback["Selector Population"]
        PostMsg --> Listener["Parent Window Message Listener"]
        Listener --> Toolbar["Update Selector Input, Tag Badge, Match Count"]
        Toolbar -->|"Click 'Use Selector'"| Apply["Auto-populate scrapeUrl / rpaStepSelector"]
    end
```

---

## 4. Feature 5: Competitive Intelligence & Technology Stack Profiling

### Cross-Domain Intelligence Architecture
```mermaid
flowchart TD
    subgraph DataSources["Indexed Data Sources"]
        ChromaStore[("ChromaDB Vector Store (crawled_knowledge)")]
        LivePage["Live Scrape / Crawl Response"]
    end

    subgraph TechProfiler["Technology Profiler Engine (Passive)"]
        LivePage --> Headers["HTTP Response Headers"]
        LivePage --> HTML["HTML DOM & Script Tokens"]
        
        Headers --> SigH["Header Signatures (Cloudflare, Vercel, CloudFront, Nginx)"]
        HTML --> SigHTML["HTML Signatures (React, Next.js, Vue, WordPress, PostHog, GA4)"]
        
        SigH --> MatchEngine["TechnologyProfiler.profile()"]
        SigHTML --> MatchEngine
        
        MatchEngine --> Categorized["TechProfileResult: { Frameworks, CMS, Analytics, Infrastructure }"]
    end

    subgraph Comparator["Multi-Domain Competitor Comparator"]
        UserSelect["User selects 2 to 5 domains (#competitorModal)"] --> CompEndpoint["POST /v1/competitors/compare"]
        CompEndpoint --> CompEngine["CompetitorComparator.compare_domains()"]
        
        ChromaStore -->|"Query documents & metadatas per domain"| CompEngine
        MatchEngine -->|"Run tech fingerprinting on domain text"| CompEngine
        
        CompEngine --> ExtractMetrics["Extract: Word count, Page volume, Value prop, Pricing signals"]
        ExtractMetrics --> MatrixBuilder["_build_markdown_table()"]
        
        MatrixBuilder --> NIM_LLM{"NIM AI Configured?"}
        NIM_LLM -->|"Yes"| StrategicAI["Synthesize AI Strategic Gaps & Positioning"]
        NIM_LLM -->|"No"| Deterministic["Heuristic Market Summary"]
        
        StrategicAI --> FullReport["Complete Benchmark Dossier"]
        Deterministic --> FullReport
    end

    subgraph ExportUI["Presentation & Export Layer"]
        FullReport --> SideBySideTable["Dashboard Side-by-Side Matrix Table"]
        FullReport --> MDDownload["Markdown Export (.md)"]
        FullReport --> ReportLab["StorageExporter.to_dossier_pdf()"]
        ReportLab --> PDFDownload["Executive Multi-Column PDF (.pdf)"]
    end
```

