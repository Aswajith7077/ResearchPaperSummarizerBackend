# ResearchPaperSummarizerBackend — Understanding Guide

> This document provides a complete, in-depth explanation of the project architecture, algorithms used, data flows, and the theoretical foundation (base paper context) behind the system.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Directory Structure](#2-directory-structure)
3. [Core Algorithms](#3-core-algorithms)
   - [3.1 Text Extraction (pdfplumber)](#31-text-extraction-pdfplumber)
   - [3.2 Text Cleaning](#32-text-cleaning)
   - [3.3 Summarization — LexRank](#33-summarization--lexrank)
   - [3.4 Keyword / Keyphrase Extraction — RAKE](#34-keyword--keyphrase-extraction--rake)
   - [3.5 Reference Extraction from PDF](#35-reference-extraction-from-pdf)
   - [3.6 Reference Link Scoring — Semantic Similarity + Authority](#36-reference-link-scoring--semantic-similarity--authority)
4. [Data Flow — End-to-End Pipeline](#4-data-flow--end-to-end-pipeline)
5. [Infrastructure & Storage](#5-infrastructure--storage)
6. [API Layer](#6-api-layer)
7. [Authentication](#7-authentication)
8. [Database Schema](#8-database-schema)
9. [Configuration & Secrets](#9-configuration--secrets)
10. [Base Paper Context](#10-base-paper-context)
11. [Dependency Map](#11-dependency-map)

---

## 1. Project Overview

This is the **backend** of a Research Paper Summarizer system named **CIDAR**. It is a **FastAPI** (Python) application that:

- Accepts one or more **research paper PDFs** uploaded by an authenticated user.
- Extracts text, cleans it, and produces a structured **Markdown summary** containing:
  - A comprehensive summary
  - Key insights
  - Methodology highlights
  - Key findings (extracted highlights)
  - Technical terms / keyphrases
  - Ranked references with clickable links
- Stores the generated Markdown summaries in **Azure Blob Storage**.
- Keeps a history of summaries per user in a **PostgreSQL** database.
- Exposes a **WebSocket** endpoint for streaming/real-time readback (partially implemented).

---

## 2. Directory Structure

```
ResearchPaperSummarizerBackend/
│
├── main.py                        # Root-level FastAPI app (legacy / alternate entry point)
├── web.py                         # (Separate web utility / Streamlit app entry)
├── pdf.py                         # Standalone PDF utility script
├── insertfile.py                  # Standalone DB insertion utility
├── referals_scrapping.py          # Standalone reference scraping helper
├── extracted_references.txt       # Temp file: references extracted from the last PDF processed
├── temp_paper.pdf                 # Temp file: uploaded PDF cached for testing
├── requirement.txt / requirements.txt  # Python dependencies (requirements.txt is canonical)
│
├── algorithms/                    # 🔬 Core NLP/ML algorithms (pure logic, no HTTP)
│   ├── __init__.py
│   ├── summarization.py           # LexRank summarization, RAKE keyword extraction, highlights
│   └── reference.py               # PDF reference extraction, web search, semantic link scoring
│
├── app/                           # 🌐 FastAPI application layer
│   ├── __init__.py
│   ├── main.py                    # Primary app entry point (registers all routers)
│   ├── dependencies.py            # Shared FastAPI dependencies (e.g., JWT auth guard)
│   ├── internal/
│   │   ├── __init__.py
│   │   └── auth.py                # Internal auth router (register / login endpoints)
│   └── routers/
│       ├── __init__.py
│       ├── users.py               # User management endpoints
│       ├── reviewer.py            # Paper upload & summary generation endpoints
│       ├── history.py             # History retrieval endpoints
│       └── websockets.py          # WebSocket endpoint for summary streaming
│
├── services/                      # ⚙️ Business logic layer (called by routers)
│   ├── __init__.py
│   ├── auth.py                    # JWT token creation/validation, password hashing, DB user ops
│   ├── reviewer.py                # Orchestrates the full PDF→Markdown pipeline
│   ├── history.py                 # Azure Blob + DB operations for history
│   └── users.py                   # User CRUD operations
│
├── models/                        # 📦 Pydantic request/response models (API layer DTOs)
│   ├── __init__.py
│   ├── users.py                   # UserDB (Pydantic), UserSignIn, UserLogin, Dummy
│   └── questions.py               # Question model
│
├── schemas/                       # 🗄️ SQLModel ORM schemas (maps to database tables)
│   ├── __init__.py
│   ├── users.py                   # UserDB SQLModel → `users` table
│   ├── history.py                 # History, AssociatedFiles SQLModel → DB tables
│   └── reviewer.py                # (Reviewer-related schema, if any)
│
├── config/                        # 🔧 Configuration & connections
│   ├── __init__.py
│   ├── config.py                  # Reads all env vars (.env): JWT, DB, Azure, SerpAPI
│   ├── dbconnection.py            # PostgreSQL engine + session factory (SQLAlchemy/SQLModel)
│   └── blobconnection.py          # Azure Blob Storage client credential setup
│
└── templates/
    └── summary.md                 # Jinja2-style Markdown template for generated summaries
```

### Key Distinctions

| Folder | Responsibility |
|--------|---------------|
| `algorithms/` | Pure NLP computation — no FastAPI, no DB. Importable standalone. |
| `app/` | HTTP layer: routing, request validation, dependency injection. |
| `services/` | Business logic: orchestrates algorithms, DB, and Blob Storage. |
| `models/` | Pydantic DTOs for request/response serialization. |
| `schemas/` | SQLModel ORM models that map directly to PostgreSQL tables. |
| `config/` | Environment-driven configuration and connection bootstrapping. |
| `templates/` | Markdown output templates filled by the reviewer service. |

---

## 3. Core Algorithms

### 3.1 Text Extraction (pdfplumber)

**File:** `algorithms/summarization.py` → `extract_text_from_pdf()`

`pdfplumber` is used instead of a simple text dump because it **preserves layout** (`layout=True`). This matters for academic PDFs because:
- Multi-column layouts are common and must be read in the correct reading order.
- Tables and captions are spatially separated and should not bleed into paragraphs.

Each page's text is extracted and concatenated with double-newlines (`\n\n`) as paragraph separators.

---

### 3.2 Text Cleaning

**File:** `algorithms/summarization.py` → `clean_text()`

A sequence of regex-based transformations handles academic paper noise:

| Pattern | What It Removes |
|---------|-----------------|
| `\([^)]*\)` | Parenthetical citations, e.g., `(Smith, 2020)` |
| `\[[^\]]*\]` | Bracket citations, e.g., `[1]`, `[REF]` |
| `\S+@\S+` | Email addresses |
| `http\S+\|www\S+` | URLs |
| `[^\S\n]+` | Excess horizontal whitespace (collapses to single space) |
| `\n\s+\n` | Blank lines with stray whitespace → clean `\n\n` |
| `[^\w\s.,;:!?'"-]` | Special characters / symbols not in normal prose |

This ensures the downstream NLP models work on clean, prose-only content.

---

### 3.3 Summarization — LexRank

**File:** `algorithms/summarization.py` → `generate_summary()`

**Library used:** `sumy` — `LexRankSummarizer`

#### What is LexRank?

LexRank is a **graph-based extractive summarization** algorithm introduced in the paper:

> *Erkan G., Radev D.R. (2004). "LexRank: Graph-Based Lexical Centrality as Salience in Text Summarization." Journal of Artificial Intelligence Research, 22, 457–479.*

**Core idea:**

1. Each sentence in the document is treated as a **node** in a graph.
2. **Edges** between sentences are weighted by their **cosine similarity** using **TF-IDF** (Term Frequency–Inverse Document Frequency) vectors.
3. An edge is added only if the cosine similarity exceeds a threshold (typically 0.1), making the graph sparse.
4. **LexRank score** is computed using a variant of the **PageRank algorithm** (or degree centrality — the simplified "continuous" LexRank variant). This is an **eigenvector centrality** computation on the similarity graph.
5. The top-N sentences by centrality score are selected as the summary.

**Why this is appropriate for research papers:**
- Research papers have a specific discourse structure. Important claims tend to be mentioned or paraphrased in multiple locations (abstract, intro, conclusion). LexRank naturally surfaces such sentences because they are semantically central to many others.
- It is **unsupervised** — no training data is needed, making it generalizable across any domain of research.

**Post-processing in this codebase:**
```python
# Remove noise first
clean_content = re.sub(r'\b(Figure|Table)\s+\d+[.:].*', '', text)
clean_content = re.sub(r'\bDOI:.+', '', clean_content)

# Run LexRank
parser = PlaintextParser.from_string(clean_content, Tokenizer("english"))
summarizer = LexRankSummarizer()
summary = summarizer(parser.document, sentences_count)

# Filter out garbage sentences
return " ".join([s for s in summary_sentences if len(s.split()) > 5 and s.endswith(('.', '!', '?'))])
```

Only sentences with **more than 5 words** that end in terminal punctuation are kept—filtering out figure captions, headers, and incomplete sentences that leak through.

---

### 3.4 Keyword / Keyphrase Extraction — RAKE

**File:** `algorithms/summarization.py` → `extract_keywords()`

**Library used:** `rake-nltk` — `Rake`

#### What is RAKE?

RAKE (Rapid Automatic Keyword Extraction) is introduced in:

> *Rose S., Engel D., Cramer N., Cowley W. (2010). "Automatic keyword extraction from individual documents." Text Mining: Applications and Theory.*

**Core idea:**

1. The text is split on **stop words** and **phrase delimiters** (punctuation). The resulting runs of non-stop words become **candidate phrases**.
2. Each word is scored using a **word frequency / word degree ratio**:
   - **Frequency**: how many times the word appears.
   - **Degree**: how often the word co-occurs with other words in candidate phrases (longer phrases give higher degree).
   - `score(word) = degree(word) / frequency(word)`
3. A phrase's score = sum of scores of its constituent words.
4. Top-scoring phrases are returned as keywords.

**Configuration in this codebase:**
```python
r = Rake(
    min_length=1,
    max_length=3,           # Only 1–3 word phrases (academic keyphrases rarely exceed 3 words)
    include_repeated_phrases=False
)
```

Phrases longer than 3 words are filtered, and only multi-word or fully-uppercase terms (e.g., acronyms) are kept as "Technical Terms".

---

### 3.5 Reference Extraction from PDF

**File:** `algorithms/reference.py` → `extract_references_from_pdf()`

This is a **heuristic, pattern-based** section locator:

1. The PDF is read page-by-page using `pdfplumber`.
2. Each page is scanned for a **"References" section heading** using a set of regex patterns:
   - `References`, `Bibliography`, `Works Cited`, `Literature Cited`, `References Cited`
3. The exact character position of the heading within the page text is stored.
4. Subsequent pages are scanned for **next-section markers** (Appendix, Acknowledgements, Notes, etc.) to determine where the references section ends.
5. Text between the start and end positions is extracted and saved to `extracted_references.txt`.

Individual references (formatted as `[1] Author...`) are then parsed by `parse_reference_as_list()` which reads the file and reassembles multi-line references by detecting `[N]` start tokens.

---

### 3.6 Reference Link Scoring — Semantic Similarity + Authority

**File:** `algorithms/reference.py` → `score_links()`, `relevance_score()`, `authority_score()`

This is the most sophisticated algorithm in the project. For each extracted reference, the system:

**Step 1: Parse the reference**
```python
parse_reference(ref_text)
# → {title, authors, year, venue}
```
Regex patterns extract the authors (before year), year (in parentheses), title (first sentence after year), and venue.

**Step 2: Search for candidate URLs**
- Primary: **Google Scholar** via SerpAPI (`search_google_scholar`)
- Fallback: **arXiv** if the venue contains an arXiv ID
- Last resort: **General Google** via SerpAPI (`search_google`)

**Step 3: Score each candidate URL**

For each URL:

**Authority Score** (`authority_score(url)`):
```
1.0  →  arxiv.org, springer.com, ieee.org, .edu, .gov
0.5  →  all other domains
```
A simple, binary domain-based trust signal.

**Relevance Score** (`relevance_score(ref_text, webpage_text)`):
Uses **cosine similarity** between two **sentence embeddings**:
```python
model = SentenceTransformer("all-MiniLM-L6-v2")
ref_embedding  = model.encode(reference_text)
page_embedding = model.encode(webpage_text[:500])
similarity = dot(ref_embedding, page_embedding) / (norm(ref) * norm(page))
```

`all-MiniLM-L6-v2` is a **bi-encoder transformer** fine-tuned for **semantic textual similarity** tasks. It maps variable-length text to a fixed 384-dimensional embedding space where semantically similar texts have high cosine similarity.

**Total Score:**
```python
total_score = authority_score * relevance_score
```

**Step 4: Rank and select top-5 links**
```python
sorted_scores = sorted(all_scores, key=lambda x: x["total_score"], reverse=True)
return sorted_scores[:5]
```

---

## 4. Data Flow — End-to-End Pipeline

```
User uploads PDF via POST /api/reviewer/upload_files/{user_id}
                │
                ▼
    app/routers/reviewer.py
        └── generate_markdown(file_data)   [services/reviewer.py]
                │
                ├─► extract_text_from_pdf()          ← pdfplumber layout-aware extraction
                │
                ├─► clean_text()                     ← Regex cleaning (citations, URLs, etc.)
                │
                ├─► generate_summary()               ← LexRank (7 sentences, comprehensive)
                ├─► generate_summary(sentences=3)    ← LexRank (3 sentences, key insights)
                │
                ├─► method_section detection         ← keyword-based paragraph filter
                │       └─► generate_summary(4)      ← LexRank on method paragraphs
                │
                ├─► extract_highlights()             ← Position + length scoring, top-5 sentences
                │
                ├─► extract_keywords()               ← RAKE keyphrase extraction (top 15)
                │
                ├─► extract_references_from_pdf()    ← Section-locator regex → file write
                ├─► parse_reference_as_list()        ← [N] pattern parser
                └─► optimize_urls()
                        ├─► parse_reference()        ← Regex: authors, year, title, venue
                        ├─► search_resource()        ← SerpAPI: Scholar → arXiv → Google
                        ├─► fetch_webpage_text()     ← BeautifulSoup HTML → plain text
                        ├─► authority_score()        ← Domain trust heuristic
                        ├─► relevance_score()        ← SentenceTransformer cosine similarity
                        └─► sorted top-5 links
                │
                ▼
    templates/summary.md   ← Jinja2-style placeholder substitution
                │
                ▼
    Return Markdown string to client (JSON response)
                │
                ▼ (optional, currently commented out)
    insert_history()       ← Store in Azure Blob + PostgreSQL history table
```

---

## 5. Infrastructure & Storage

### PostgreSQL (via SQLAlchemy + SQLModel)

- **Connection string:** `postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}?sslmode=require`
- **ORM:** SQLModel (combines SQLAlchemy + Pydantic)
- **Tables auto-created** on startup via `SQLModel.metadata.create_all(engine)`
- `NullPool` is used — no connection pooling, each request gets a fresh connection (suitable for serverless / cloud environments)

### Azure Blob Storage

- **Auth:** Service Principal (`ClientSecretCredential` — client_id, client_secret, tenant_id)
- **Usage:** Summaries are stored as `.md` blobs with path pattern: `{user_id}/{date}/{title}/{timestamp}.md`
- **Read back:** History endpoints retrieve the blob by reconstructing the filename stored in PostgreSQL.

---

## 6. API Layer

### Routers registered in `app/main.py`

| Router | Prefix | Description |
|--------|--------|-------------|
| `internal/auth.py` | `/api` | Login, Register |
| `routers/users.py` | `/api/users` | User profile endpoints |
| `routers/reviewer.py` | `/api/reviewer` | PDF upload + summary |
| `routers/history.py` | `/api/history` | History retrieval |
| `routers/websockets.py` | `/api/websocket` | WebSocket streaming |

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/reviewer/upload_files/{user_id}` | Upload PDF(s), returns generated Markdown |
| `GET` | `/api/reviewer/list_history_today` | (Stub) List today's summaries |
| `POST` | `/api/reviewer/add_question` | Add a question to the queue |
| `WS` | `/api/websocket/summarize` | Stream summary via WebSocket |

### WebSocket Flow
1. Client connects and sends a **schedule key** (obtained earlier via a scheduling API).
2. Server looks up the pending job in `schedule_queue` (an in-memory dict).
3. Sends back the Markdown content and closes the connection.

> **Note:** The current WebSocket implementation sends a hardcoded placeholder template. The actual content delivery using the schedule queue is partially scaffolded.

---

## 7. Authentication

**Library:** `PyJWT` + `passlib[bcrypt]`

- Passwords are hashed with **bcrypt** (industry-standard adaptive hash).
- Two JWT tokens are issued:
  - **Access token** — short-lived, for API requests. Signed with `JWT_ACCESS_TOKEN_SECRET_KEY`.
  - **Refresh token** — longer-lived, for re-issuing access tokens. Signed with `JWT_REFRESH_TOKEN_SECRET_KEY`.
- Algorithm configured via env (`JWT_ENCODE_ALGORITHM`, typically `HS256`).
- `app/dependencies.py` provides `check_access_token` as a FastAPI `Depends()` guard used on protected routers.

---

## 8. Database Schema

### `users` table (`schemas/users.py` → `UserDB`)

| Column | Type | Notes |
|--------|------|-------|
| `username` | `str` | **Primary Key** |
| `email` | `str` | Unique, not null |
| `password` | `str` | bcrypt hash |
| `fullname` | `str` | Default: `"GuestUser"` |
| `is_logged` | `bool` | Login state flag |
| `lastlogin` | `datetime` | Optional, updated on login |
| `role` | `str` | Default: `"customer"` |

### `history` table (`schemas/history.py` → `History`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID` | Primary Key |
| `user_id` | `str` | Foreign Key → `users.username` |
| `date` | `str` | `dd-mm-yyyy` |
| `title` | `str` | PDF filename used as title |
| `filename` | `str` | Full Azure Blob path |
| `timestamp` | `str` | ISO timestamp |

### `associated_files` table (`schemas/history.py` → `AssociatedFiles`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | `UUID` | Primary Key |
| `history_id` | `UUID` | Foreign Key → `history.id` |
| `filename` | `str` | Original uploaded filename |

---

## 9. Configuration & Secrets

All configuration is loaded from a `.env` file via `python-dotenv`. Variables read in `config/config.py`:

| Variable | Purpose |
|----------|---------|
| `JWT_ENCODE_ALGORITHM` | JWT algorithm (e.g., `HS256`) |
| `JWT_ACCESS_TOKEN_SECRET_KEY` | Access token signing secret |
| `JWT_REFRESH_TOKEN_SECRET_KEY` | Refresh token signing secret |
| `JWT_ACCESS_TOKEN_EXPIRE_TIME_MINUTES` | Access token TTL |
| `JWT_REFRESH_TOKEN_EXPIRE_TIME_MINUTES` | Refresh token TTL |
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | PostgreSQL connection |
| `SERPAPI` | SerpAPI key for Google Scholar / Google search |
| `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` | Azure Service Principal |
| `AZURE_STORAGE_URL`, `AZURE_CONTAINER_NAME` | Azure Blob Storage target |

---

## 10. Base Paper Context

The summarization pipeline in this project directly implements and builds upon algorithms from two foundational NLP papers:

---

### 📄 Primary Algorithm: LexRank (2004)

**Citation:**
> Erkan, G., & Radev, D. R. (2004). **LexRank: Graph-Based Lexical Centrality as Salience in Text Summarization.** *Journal of Artificial Intelligence Research*, 22, 457–479.

**Key concepts used:**
- TF-IDF sentence vectors
- Cosine similarity edge-weighted sentence graph
- PageRank / eigenvector centrality for sentence scoring
- Extractive summarization (select sentences verbatim, no text generation)

This is implemented via the `sumy` library's `LexRankSummarizer`. The `PlaintextParser` tokenizes the cleaned paper text into sentences, and the LexRankSummarizer operates on the `Document` object to return the top-N most central sentences.

---

### 📄 Keyword Extraction Algorithm: RAKE (2010)

**Citation:**
> Rose, S., Engel, D., Cramer, N., & Cowley, W. (2010). **Automatic keyword extraction from individual documents.** In *Text Mining: Applications and Theory* (pp. 1–20). Wiley.

**Key concepts used:**
- Stop-word-based phrase candidate generation
- Word co-occurrence degree scoring
- Ratio of degree to frequency for final word scores
- Phrase score = sum of word scores

This is implemented via `rake-nltk`'s `Rake` class. The phrases extracted serve as both general keywords and technical terms filtering (acronyms and multi-word terms).

---

### 📄 Semantic Similarity Model: Sentence-BERT (2019)

**Citation:**
> Reimers, N., & Gurevych, I. (2019). **Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks.** *Proceedings of EMNLP 2019*.

**Specific model used:** `all-MiniLM-L6-v2` (a distilled, efficient variant fine-tuned for semantic similarity)

**Key concepts used:**
- Bi-encoder transformer architecture
- Fixed-size sentence embeddings (384 dimensions)
- Cosine similarity for semantic relevance measurement

This powers the reference link scoring system. Given a reference string and scraped webpage text, cosine similarity between their embeddings determines how semantically relevant a candidate URL is to the original reference.

---

### How the Algorithms Interconnect

```
Input PDF
    │
    ▼
pdfplumber (layout-aware extraction)
    │
    ▼
Regex cleaning (remove citations, URLs, symbols)
    │
    ├──► LexRank  ─────────────────────► Comprehensive summary, Key insights, Methodology
    │
    ├──► RAKE ────────────────────────► Keywords, Technical Terms
    │
    ├──► Position/Length heuristic ──► Key Findings (highlights)
    │
    └──► Reference extractor
              │
              ├── Regex parser → title/authors/year/venue
              ├── SerpAPI → candidate URLs
              ├── BeautifulSoup → webpage text
              └── SentenceTransformer (MiniLM) → semantic relevance score
                                                    + Domain authority score
                                                    → Top-5 ranked reference links
```

---

## 11. Dependency Map

```
app/main.py
  ├── config/dbconnection.py         (engine, create_tables, SessionDepends)
  ├── app/internal/auth.py           (login/register router)
  │     └── services/auth.py         (Authenticate, JWT, bcrypt)
  │           └── schemas/users.py   (UserDB SQLModel)
  ├── app/routers/reviewer.py        (upload endpoint)
  │     ├── services/reviewer.py     (generate_markdown, schedule)
  │     │     ├── algorithms/summarization.py  (LexRank, RAKE, pdfplumber)
  │     │     └── algorithms/reference.py      (reference extractor, SentenceTransformer)
  │     └── services/history.py      (insert_history, Azure Blob)
  │           └── config/blobconnection.py     (Azure ClientSecretCredential)
  ├── app/routers/users.py
  │     └── services/users.py
  └── app/routers/history.py
        └── services/history.py
```

---

*Generated: 2026-03-10 | Project: ResearchPaperSummarizerBackend (CIDAR)*
