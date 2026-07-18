# GenAI Agent for Data Pipeline Design Assistance

Built at the **TCS AI Hackathon** — a RAG-based assistant that helps answer questions about data pipelines and schemas, using both a fixed knowledge base and whatever files you upload at it (CSV, JSON, Excel, or raw SQL).

The idea started from a simple pain point: when you're designing a data pipeline, you're constantly flipping between company policy docs and your own dataset to check things like "does this column follow our naming convention?" or "what's the schema of this table?" This tool puts both in one chat window.

## What it actually does

You upload a file (or a few), ask a question in plain English, and it digs through both:
- A **corporate knowledge base** of markdown docs (rules, standards, conventions — whatever your org has documented)
- **Your uploaded data** (parsed and chunked so it can be searched)

...and gives you an answer, along with the actual snippets it used to get there, so you can verify it's not making things up.

If you ask something totally unrelated to your data or the knowledge base (like a general trivia question), it'll tell you it can't help with that instead of guessing.

## Methodology

**Hybrid retrieval instead of picking one source.** Company docs are static and don't change often, but your uploaded data is temporary and session-specific. Rather than treating them the same, the app runs two separate retrievers — one over the knowledge base, one over your uploaded files — and blends the results using LangChain's `EnsembleRetriever` (60% weight to the knowledge base, 40% to your data). This gave noticeably better answers than dumping everything into one vector store.

**Sessions don't leak into each other.** Each set of uploaded files gets its own isolated ChromaDB vector store, keyed off the uploaded files themselves. So if two people are using the app (or you upload two different datasets), one person's data never bleeds into another's context.

**You can tell where an answer came from.** Every response shows the source chunks it pulled from — tagged as either coming from the knowledge base or your uploaded file — with a small preview so you can double check it.

## Tech stack

- **Streamlit** — the interface
- **LangChain** — orchestration, prompt handling, retrieval
- **ChromaDB** — vector storage (both for the knowledge base and per-session user data)
- **SQLite** — in-memory schema extraction for SQL uploads
- **OpenAI-compatible LLM & embedding endpoints** — configurable via environment variables, so it's not locked to one provider

## Getting it running

1. Clone the repo and install dependencies:
   ```bash
   pip install streamlit pandas httpx langchain-text-splitters langchain-openai langchain-community langchain-classic python-dotenv openpyxl
   ```

2. Create a `.env` file in the project root with your LLM and embedding config:
   ```env
   LLM_BASE_URL=your_llm_endpoint
   LLM_MODEL=your_model_name
   LLM_API_KEY=your_api_key

   EMBEDDING_BASE_URL=your_embedding_endpoint
   EMBEDDING_MODEL=your_embedding_model
   EMBEDDING_API_KEY=your_embedding_api_key
   ```

3. Add your knowledge base docs (markdown files) into a folder called `kb_docs/` in the project root.

4. Run it:
   ```bash
   streamlit run app.py
   ```

5. Open the sidebar, upload a CSV, JSON, Excel, or SQL file, and start asking questions in the chat box.

## Additionally,

- The knowledge base is loaded and embedded once when the app starts, so keep `kb_docs/` populated before launch.
- Vector stores are written to disk (`./kb_index` for the knowledge base, `./user_index/session_*` per upload session), so repeated runs won't need to re-embed the knowledge base every time.

## Where this landed

This was built and demoed as a prototype at the TCS AI Hackathon, where it received appreciation from the jury for the approach to hybrid retrieval and multi-format data ingestion.
