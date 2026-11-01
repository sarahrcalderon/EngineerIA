# EngineerIA

**AI-powered customer support for Empório da Música**  
Technical challenge submission | Python, React, local LLM, and evidence-grounded retrieval

## 1. Project overview

EngineerIA is a conversational assistant designed to answer customer questions about a music store. It helps visitors explore products and categories, check listed prices and availability, discover recorded promotions, and understand store policies. Answers are grounded in information explicitly approved for customer-facing use rather than unrestricted access to the source files.

The application combines a React/TypeScript chat interface, a Python/FastAPI service, structured catalog retrieval from SQLite, policy retrieval using SQLite FTS5, and a locally hosted Ollama model (`qwen3:4b`). The initial goal is a reproducible, maintainable solution that can run without paid AI APIs or mandatory Docker infrastructure.

## 2. Technology choices and rationale

| Component | Choice | Why |
| --- | --- | --- |
| User interface | React + TypeScript + Vite | Component-based UI, reusable chat/product cards, type safety, and a lightweight development workflow. |
| Backend | Python 3.12+ + FastAPI | Strong fit for LLM orchestration and data processing; typed API contracts, automatic API documentation, and straightforward testing. |
| Local language model | Ollama + `qwen3:4b` | Local inference without paid API dependencies; tool-calling capability and control over the model runtime. |
| Structured storage | SQLite (STRICT tables) | Simple, portable, serverless persistence appropriate for a self-contained technical challenge. |
| Document retrieval | SQLite FTS5 | Lightweight full-text search for indexed store-policy excerpts, without an external vector database. |
| Testing and quality | pytest, Ruff, Vitest, ESLint, Prettier | Repeatable regression tests and consistent code quality across both stacks. |

The architecture emphasizes clear boundaries between domain rules, application orchestration, infrastructure adapters, and HTTP/UI presentation. This separation makes the project easier to test, maintain, and extend.

## 3. Architecture and request flow

```text
Customer -> React/TypeScript chat -> FastAPI
                                   |
                                   v
                           Application orchestrator
                              /           \
                             v             v
                    Ollama qwen3:4b    Read-only tools
                                          |
                              +-----------+-----------+
                              |                       |
                       SQLite catalog            SQLite FTS5
                       and promotions            policy excerpts
                              |                       |
                              +-----------+-----------+
                                          |
                              Publication/evidence filter
                                          |
                                Grounded API response
                                          |
                                  Chat and product cards
```

The frontend communicates with the backend, not directly with the local model or source database. Catalog queries use controlled, read-only operations. Store-policy questions retrieve relevant indexed excerpts with source metadata. The assistant may only use evidence approved by the local publication control.

## 4. Data ingestion and retrieval design

- Operational data originate from six private CSV datasets: categories, customers, products, orders, order items, and promotions. Customer and order records are **not exposed to the assistant's customer-facing tools**.
- Imports are validated and transactional. Monetary amounts are represented in integer cents to avoid floating-point pricing errors.
- The store-policy PDF is segmented and indexed into searchable excerpts with source metadata (such as page references). The entire PDF is not provided to customers.
- Structured product queries support category, availability, price bounds, ordering, and result limits. Ordering is performed deterministically in the backend, rather than asking the LLM to sort free-form text.
- A publication manifest authorizes only selected customer-facing evidence. In the validated local setup, **106 evidence entries** were approved. This authorization is **local-development-only**, not permission to publish the underlying datasets or documents.
- Promotions are reported with appropriate caution where current validity cannot be verified.

**Retrieval strategy:** use structured database queries for factual catalog data and full-text search for policy passages. This avoids treating prices or inventory as unstructured semantic-search content and keeps provenance attached to policy answers.

## 5. LLM and prompting strategy

The locally hosted `qwen3:4b` model interprets natural-language requests and can call constrained, read-only tools. The application controls tool schemas, validates arguments, enforces limits, filters evidence, and assembles the customer-facing result.

Prompting and orchestration principles:

1. Answer only from approved catalog, promotion, or policy evidence when making factual store claims.
2. Handle greetings naturally without requiring a database lookup.
3. Select structured retrieval for questions involving categories, price comparisons, availability, and quantities.
4. Avoid inventing prices, stock, discount validity, shipping promises, or policy conditions.
5. Ask for clarification when a reference is ambiguous; otherwise report when authorized information is unavailable.
6. Never expose raw SQL, internal tool details, customer/order data, or original private documents.

The interface formats authorized products as readable cards with Brazilian-real prices. Product imagery, when present without verified source photographs, must be labeled as illustrative.

## 6. Repository layout (conceptual)

```text
EngineerIA/
  backend/            FastAPI application, orchestration, adapters, tests
  frontend/           React + TypeScript + Vite chat interface
  docs/               Architecture notes and validation reports
  data/               Private input datasets and policy PDF (do not commit)
  .local/             Private local database/publication artifacts (do not commit)
  README.md           Project documentation
```

Internal module and file names may differ; use the checked-out repository as the source of truth.

## 7. Requirements and local setup

**Prerequisites:** Python 3.12 or newer, Node.js and npm compatible with the frontend's `package.json`, Git, and Ollama installed locally. Download the `qwen3:4b` model before running the application. The commands below reflect the tested Windows/Git Bash workflow; other systems require equivalent paths and environment activation.

### 7.1 Obtain the model

```bash
ollama pull qwen3:4b
ollama list
curl http://127.0.0.1:11434/api/tags
```

Ollama must be running and accessible at `http://127.0.0.1:11434`. If its service is already listening, do not start a second `ollama serve` process.

### 7.2 Backend

From the project root, install dependencies using the dependency manifest actually included in `backend/` (for example, `requirements.txt` or `pyproject.toml`). Create a Python virtual environment if one is not already configured. Then run, on Windows/Git Bash:

```bash
cd backend
./.venv/Scripts/python.exe -m uvicorn emporio_ia.principal:aplicacao \
  --host 127.0.0.1 --port 8001 --log-level info --access-log
```

Check health:

```bash
curl -i http://127.0.0.1:8001/api/saude
```

A healthy instance should return HTTP 200. If port 8001 is occupied, inspect the existing process before starting another instance. Keep the backend process running while testing the frontend.

### 7.3 Frontend

In a separate terminal:

```bash
cd frontend
npm install
VITE_API_URL=http://127.0.0.1:8001 npm run dev
```

Open the local URL printed by Vite (commonly `http://localhost:5173`). The frontend must point to the same backend port, and backend CORS settings must allow the active local frontend origin.

### 7.4 Private data and publication configuration

The project requires its private source files and local import/index/publication setup to be prepared according to the repository's internal documentation. **Do not commit or distribute `data/`, `.local/`, private SQLite files, original CSV datasets, or the full policy PDF.** The local evidence manifest must be present and explicitly approved; without it, the safety filter can correctly withhold all evidence and the assistant will not be able to answer factual store questions.

Exact environment variable names, ingestion commands, and dependency-install commands should be checked against the current repository configuration before submission; they are intentionally not invented here.

## 8. Tests and validation

Backend test command (Windows/Git Bash, from `backend/`):

```bash
./.venv/Scripts/python.exe -m pytest testes -q
```

Real Ollama integration tests (when the model and approved local data are available):

```bash
EMPORIO_TESTAR_OLLAMA_REAL=1 ./.venv/Scripts/python.exe \
  -m pytest testes/atendimento/test_ollama_real.py -v -rs
```

Frontend scripts are defined in `frontend/package.json`; typical checks include:

```bash
npm run build
npm run lint
npm run test
```

**Latest reported local validation:** 374 backend tests, 71 frontend tests, and 12 real-Ollama scenarios passed; build, lint, and formatting checks also passed. These are reported results from the local development workflow, not independently rerun for this document. The validation scope was local development, not production deployment.

Suggested manual acceptance checks include greetings; catalog browsing; cheapest/most expensive products; price and availability filters; promotions; exchange/return/warranty/payment/delivery policies; multi-turn context; unavailable items; and attempts to request private customer/order data.

## 9. Known limitations

- **Local-only validation:** no production deployment, security review, or load testing is claimed.
- **Small local model:** natural-language interpretation may be conservative or inconsistent for unusual phrasing and complex multi-intent requests.
- **Data freshness:** availability, prices, and promotions reflect the imported snapshot; promotional validity may require separate verification.
- **Limited conversation context:** follow-up references and multi-step shopping discussions require continued evaluation.
- **Evidence scope:** the assistant can only answer from approved evidence; missing or unpublished information must remain unavailable.
- **Product imagery:** where the dataset lacks authentic product images, illustrative images must not be represented as exact product photographs.
- **Environment reproducibility:** the private data and publication manifest are deliberately excluded from public distribution, so a reviewer needs an approved local fixture or documented setup path to reproduce all data-dependent scenarios.

## 10. What I would improve with more time

1. Expand end-to-end evaluation with a fixed set of realistic customer conversations and quality metrics for groundedness, tool choice, and multi-turn consistency.
2. Add robust conversational context handling for pronouns, follow-up product comparisons, and mixed questions.
3. Add a safe administrative workflow for reviewing and approving customer-visible evidence, with audit records.
4. Improve catalog freshness and promotion-validity checks through controlled synchronization.
5. Add observability for model latency, tool usage, retrieval misses, and error categories without logging sensitive content.
6. Expand accessibility, mobile usability, and verified product-image support.
7. Package a sanitized demo dataset and automated setup to make evaluation easier without exposing private files.

## 11. Use of AI coding assistants

I used **OpenAI Codex** as a development assistant while working on EngineerIA. Its role was to help me organize and refine the code structure, explore implementation approaches, and implement improvements in code I was developing. I used it as a collaborative coding tool, not as a replacement for understanding the architecture or checking the results.

My workflow involved defining requirements and constraints, reviewing suggested changes, running the application locally, testing behavior with real user questions, and iterating on defects identified during validation. Examples of these iterations include improving the conversational experience, fixing evidence publication behavior, refining product-card presentation, and supporting structured catalog queries. I retained responsibility for technical decisions, integration, validation, and the final submission.

AI-generated suggestions were subject to the same review, tests, and security constraints as manually written code. In particular, the project keeps private input data outside version control and restricts what the customer-facing assistant is allowed to retrieve.

## 12. Security and scope

EngineerIA is a **read-only, evidence-grounded customer-support prototype**. It is not a checkout system and does not provide customer account access, order-management operations, arbitrary SQL execution, shell access, or unrestricted document access. Local publication authorization must not be interpreted as permission to release confidential data publicly.

---

**Submission note:** This README documents the implementation and locally reported validation. Before submitting, verify that dependency filenames, environment variables, scripts, and repository paths match the final checked-out source tree.
