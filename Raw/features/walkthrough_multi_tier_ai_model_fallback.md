# Walkthrough - Multi-Tier AI Model Fallback & Universal Loading Timers

**Date & Time**: 22-Sep-2026 03:26

## Summary of Completed Work

In response to the user's feedback:
> *"what i can see this is loading since 4 more minutes. also i want wherever loading shows i want start time and timer to be visiable to user"*
> *"then can we move to next alternative model or different model to get quicker things. Also make sure things should be faster and proper. So find alternative models if timeout or fails"*

We resolved both issues:
1. **Identified & Fixed the 4+ Minute Dossier Synthesis Stall**:
   - The user screenshot revealed the **Multi-Competitor Market Intelligence Dossier** was stalled querying `moonshotai/kimi-k3` because the remote NVIDIA NIM endpoint was queued/timing out.
   - We upgraded `DossierGenerator` (`src/ethical_crawler/knowledge/dossier_generator.py`) with a resilient multi-tier fallback chain (`deepseek-ai/deepseek-v4.1-flash` &rarr; `meta/llama-3.2-11b-vision-instruct` &rarr; `nvidia/nemotron-3.5-lightning-30b-a3b`), per-call timeouts (22.0s / 20.0s), and fallback to DeepSeek `reasoning_content` if `content` is empty.
   - Changed the default recommended synthesis model to **`deepseek-ai/deepseek-v4.1-flash`** across both UI dropdowns and backend defaults, delivering full cross-domain dossiers in **~15 seconds**.

2. **Universal Start Time & Live Elapsed Timers Across All Loading States**:
   - Implemented a unified live timer system (`createLiveTimer` & `formatTimerSeconds`) that shows the exact start time (`Started: HH:MM:SS AM/PM`) and a live elapsed counter (`Elapsed: MM:SS` ticking every 1,000ms) across every loading surface in the application.

---

## 1. Universal Loading Timers Architecture

Every operational workflow now provides clear visual timing feedback:

| Component | UI Location | Start Timestamp | Live Elapsed Timer | Behavior on Completion |
| :--- | :--- | :--- | :--- | :--- |
| **Main Crawler & Scraper** | Top Right of `#statusCard` Banner | `#statusStartTime` | `#statusElapsedTime` (ticking every 1s) | Freezes on final elapsed time (e.g. `00:28`) |
| **Market Intelligence Dossier** | Inside `#dossierLoading` Card | `#dossierStartTime` | `#dossierElapsedTime` (ticking every 1s) | Metadata pill logs final duration (`15s`) |
| **Single-Page AI Extractor** | Modal Preview beside Action Button | `#modalAiStartTime` | `#modalAiElapsedTime` (ticking every 1s) | Badge hidden on modal close or reset |
| **Knowledge Base Ask AI (RAG)** | Inside `#askLoading` Card | `#askStartTime` | `#askElapsedTime` (ticking every 1s) | Displays alongside cited sources |
| **Semantic Vector Search** | Inside `#searchResultsContainer` | Search launch timestamp | Rendered in loading container | Replaced by similarity ranking cards |

### Timing Engine in Frontend (`app.py`):
```javascript
function formatTimerSeconds(sec) {
  const m = Math.floor(sec / 60).toString().padStart(2, '0');
  const s = (sec % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

function createLiveTimer(startTimeElemId, elapsedTimeElemId) {
  const startObj = new Date();
  const startTimeStr = startObj.toLocaleTimeString();
  const startElem = document.getElementById(startTimeElemId);
  const elapsedElem = document.getElementById(elapsedTimeElemId);
  if (startElem) startElem.innerText = startTimeStr;
  if (elapsedElem) elapsedElem.innerText = '00:00';

  let seconds = 0;
  const intervalId = setInterval(() => {
    seconds++;
    if (elapsedElem) elapsedElem.innerText = formatTimerSeconds(seconds);
  }, 1000);

  return {
    intervalId: intervalId,
    stop: () => {
      clearInterval(intervalId);
      return { startedAt: startTimeStr, totalSeconds: seconds, elapsedFormatted: formatTimerSeconds(seconds) };
    }
  };
}
```

---

## 2. Multi-Tier AI Waterfall Implementation

### In `AIExtractor` (`src/ethical_crawler/extractors/ai_extractor.py`):
- Strict **18.0s** primary model timeout.
- Automatic rollover to:
  1. `deepseek-ai/deepseek-v4.1-flash` (15.0s timeout)
  2. `meta/llama-3.2-11b-vision-instruct` (15.0s timeout)
  3. `nvidia/nemotron-3.5-lightning-30b-a3b` (15.0s timeout)
- High-level audit logs and transparent model tag `r.ai_model_used`.

### In `DossierGenerator` (`src/ethical_crawler/knowledge/dossier_generator.py`):
- Added `httpx.Timeout(30.0, connect=8.0)` to client.
- Strict **22.0s** synthesis timeout with automated rollover across the fallback waterfall chain.
- Automatic detection of `choice.message.reasoning_content` to guarantee that hybrid reasoning models (like DeepSeek) never produce empty dossiers.
- Benchmark verified: 4,014 bytes comprehensive dossier produced in **15.70s**!

---

## 3. Verification & Validation Results

1. **Automated Unit Tests**:
   - `pytest tests/`: **47 passed in 28.04s** (100% pass rate).
2. **Code Quality & Linter**:
   - `ruff check .`: 0 errors.
   - `ruff format --check .`: 0 errors (all 61 files formatted).
3. **Database Integrity**:
   - ChromaDB vector store preserved with zero destructive operations.
