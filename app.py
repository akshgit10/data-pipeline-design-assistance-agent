import streamlit as st
import pandas as pd
import os
import httpx
from glob import glob
import json
import sqlite3
import re
from dotenv import load_dotenv

# Modern Core and Splitter Packages
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.prompts import PromptTemplate

# Legacy Chain Bridge Layer
from langchain_classic.chains import RetrievalQA

# -------------------------------
# Load Environment Configuration
# -------------------------------
load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY")

EMBEDDING_BASE_URL = os.getenv("EMBEDDING_BASE_URL")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY")

os.environ["TIKTOKEN_CACHE_DIR"] = "./token"

# Target API client configuration
client = httpx.Client(verify=False)

# -------------------------------
# Modern Streamlit Page Setup
# -------------------------------
st.set_page_config(
    page_title="Data Pipeline Architect",
    page_icon="⚙️",
    layout="wide"
)

# Custom CSS for polished layout typography
st.markdown("""
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .source-card-kb {
        padding: 10px;
        border-left: 4px solid #3B82F6;
        background-color: #EFF6FF;
        margin-bottom: 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .source-card-user {
        padding: 10px;
        border-left: 4px solid #10B981;
        background-color: #ECFDF5;
        margin-bottom: 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Sidebar Architecture Display
# -------------------------------
with st.sidebar:
    st.markdown("### 🛠️ Pipeline Architecture")
    st.caption("Production configuration state used for runtime context injections.")
    
    st.markdown("---")
    st.markdown("**LLM Engine:**")
    st.code(LLM_MODEL if LLM_MODEL else "OpenAI Chat Model", language="text")
    
    st.markdown("**Vector Store Tiering:**")
    st.info("Hybrid Retrieval Vector Engine Active (Ensemble: 60% Corporate KB / 40% Operational Schemas)")
    
    st.markdown("---")
    uploaded_files = st.file_uploader(
        "Ingest Data Entities", 
        type=["csv", "json", "xlsx", "sql"], 
        accept_multiple_files=True
    )

# Main Workspace Headers
st.markdown('<div class="main-title">GenAI Agent for Data Pipeline Assistance</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Automated structural schema extraction and rule-compliance evaluation</div>', unsafe_allow_html=True)

# -------------------------------
# Static Corporate Knowledge Base Initialization
# -------------------------------
if "kb_vectordb" not in st.session_state:
    with st.spinner("Initializing system base compliance parameters..."):
        kb_files = glob("kb_docs/*.md")
        kb_texts = [open(f, "r", encoding="utf-8").read() for f in kb_files]

        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
        kb_chunks = splitter.split_text("\n".join(kb_texts))

        kb_embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",  
            openai_api_key="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",  
            openai_api_base="https://models.inference.ai.azure.com"
        )

        kb_vectordb = Chroma.from_texts(
            kb_chunks,
            kb_embeddings,
            persist_directory="./kb_index",
            metadatas=[{"source": "KB"} for _ in kb_chunks]
        )
        st.session_state.kb_vectordb = kb_vectordb

# -------------------------------
# User Document Processing Engine
# -------------------------------
user_vectordb = None

if uploaded_files:
    session_dir = f"./user_index/session_{hash(str(uploaded_files))}"
    if not os.path.exists(session_dir):
        all_rows_text = []
        for upload_file in uploaded_files:
            try:
                # CSV File Handler
                if upload_file.type == "text/csv":
                    df = pd.read_csv(upload_file)
                    rows_text = df.astype(str).apply(lambda x: " | ".join(x), axis=1).tolist()
                    all_rows_text.extend([f"File: {upload_file.name} | {text}" for text in rows_text])
                
                # JSON File Handler
                elif upload_file.type == "application/json":
                    data = json.load(upload_file)
                    rows_text = [f"{k}: {v}" for k, v in data.items()]
                    all_rows_text.extend([f"File: {upload_file.name} | {text}" for text in rows_text])
                
                # Excel Spreadsheet Handler
                elif "spreadsheetml" in upload_file.type or upload_file.name.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(upload_file)
                    rows_text = df.astype(str).apply(lambda x: " | ".join(x), axis=1).tolist()
                    all_rows_text.extend([f"File: {upload_file.name} | {text}" for text in rows_text])
                
                # SQL Query & Structural DDL Engine Handler
                elif upload_file.type == "application/octet-stream" and upload_file.name.endswith(".sql"):
                    with upload_file as f:
                        sql_script = f.read().decode("utf-8")
                    
                    try:
                        # Fallback Mode 1: In-memory simulation environment via SQLite
                        conn = sqlite3.connect(":memory:")
                        
                        def sqlite_split_part(string, delimiter, part_num):
                            if not string:
                                return ""
                            parts = string.split(delimiter)
                            idx = int(part_num) - 1
                            return parts[idx] if 0 <= idx < len(parts) else ""
                        
                        conn.create_function("split_part", 3, sqlite_split_part)
                        conn.executescript(sql_script)
                        
                        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table';", conn)['name']
                        for t in tables:
                            schema = pd.read_sql(f"PRAGMA table_info({t})", conn)
                            rows_text = [f"Table {t}: {schema.to_dict(orient='records')}"]
                            all_rows_text.extend([f"File: {upload_file.name} | {text}" for text in rows_text])
                        conn.close()
                        
                    except sqlite3.OperationalError:
                        # Fallback Mode 2: Enhanced Parentheses-Aware Regex Tokenizer 
                        table_matches = re.findall(
                            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\`\"]?(\w+)[\`\"]?\s*\((.*?)\);", 
                            sql_script, 
                            re.DOTALL | re.IGNORECASE
                        )
                        
                        if table_matches:
                            for table_name, body in table_matches:
                                columns = []
                                # Regex-based delimiter split safely bypassing punctuation inside data declarations like dec(15,2)
                                raw_lines = re.split(r',\s*(?![^()]*\))', body.strip())
                                
                                for line in raw_lines:
                                    line = line.strip().replace("`", "").replace('"', '')
                                    if not line or line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "KEY", "CONSTRAINT", "UNIQUE")):
                                        continue
                                    
                                    parts = line.split(maxsplit=1)
                                    if parts:
                                        col_name = parts[0]
                                        col_type = parts[1].split()[0] if len(parts) > 1 else "UNKNOWN"
                                        
                                        # Recapture dangling characters if attributes follow functional types
                                        if "(" in parts[1] and ")" not in col_type:
                                            col_type = parts[1].split(")")[0] + ")"
                                            
                                        columns.append({
                                            "cid": len(columns), 
                                            "name": col_name, 
                                            "type": col_type
                                        })
                                
                                rows_text = [f"Table {table_name}: {columns}"]
                                all_rows_text.extend([f"File: {upload_file.name} | {text}" for text in rows_text])
                        else:
                            st.sidebar.warning(f"Could not automatically parse structural entities inside {upload_file.name}")
                else:
                    st.sidebar.error(f"Unsupported format: {upload_file.name}")
                    continue
            except Exception as e:
                st.sidebar.error(f"Error reading {upload_file.name}: {str(e)}")
                continue

        if all_rows_text:
            splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
            user_chunks = splitter.split_text("\n".join(all_rows_text))

            user_embeddings = OpenAIEmbeddings(
                model=EMBEDDING_MODEL,  
                openai_api_key=EMBEDDING_API_KEY,  
                openai_api_base=EMBEDDING_BASE_URL
            )

            user_vectordb = Chroma.from_texts(
                user_chunks,
                user_embeddings,
                persist_directory=session_dir,
                metadatas=[{"source": "USER", "file": chunk.split("|")[0].strip() if "|" in chunk else upload_file.name} for chunk in user_chunks]
            )
    else:
        user_embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL,  
            openai_api_key=EMBEDDING_API_KEY,  
            openai_api_base=EMBEDDING_BASE_URL
        )
        user_vectordb = Chroma(persist_directory=session_dir, embedding_function=user_embeddings)

# -------------------------------
# Runtime Execution RAG Engine
# -------------------------------
if "rag_chain" not in st.session_state or (user_vectordb and "user_db_loaded" not in st.session_state):
    if user_vectordb:
        kb_retriever = st.session_state.kb_vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 3})
        user_retriever = user_vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        combined_retriever = EnsembleRetriever(retrievers=[kb_retriever, user_retriever], weights=[0.6, 0.4])

        llm = ChatOpenAI(
            base_url=LLM_BASE_URL,
            model=LLM_MODEL,
            api_key=LLM_API_KEY,
            http_client=client
        )

        strict_template = """You are an expert Data Pipeline Design Assistant. Your task is to answer the query by analyzing the provided context documents or structured data records.

If the query asks for an analysis, summary, database schema design, or insights based on the uploaded data, use the context records to generate the requested technical response.

However, if the query is completely unrelated to the provided data or knowledge base (such as general knowledge, news, or unrelated historical facts), state clearly: "I cannot find the answer to this question in the uploaded files or knowledge base."

Context:
{context}

Query: {question}
Answer:"""
        
        STRICT_PROMPT = PromptTemplate(
            template=strict_template, input_variables=["context", "question"]
        )

        st.session_state.rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=combined_retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": STRICT_PROMPT}
        )
        st.session_state.user_db_loaded = True

# -------------------------------
# Interactive Interface Terminal
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat container workspace
chat_container = st.container()

with chat_container:
    for role, msg, *extra in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg)
            # Render cached source data inside expander if available in history state
            if role == "assistant" and extra:
                sources = extra[0]
                if sources:
                    with st.expander("🔍 Explored Context Sources"):
                        for doc in sources:
                            src = doc.get("source", "Unknown")
                            file_name = doc.get("file", "Unknown")
                            preview = doc.get("content", "")
                            if src == "KB":
                                st.markdown(f'<div class="source-card-kb"><strong>Corporate Policy Document:</strong><br/>{preview}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="source-card-user"><strong>File: {file_name}</strong><br/>{preview}</div>', unsafe_allow_html=True)

# User Query Execution Area
if prompt := st.chat_input("Ask a design question about your data schemas..."):
    with chat_container:
        st.chat_message("user").markdown(prompt)
    
    if "rag_chain" in st.session_state:
        with chat_container:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                with st.spinner("Analyzing ruleset mappings..."):
                    response = st.session_state.rag_chain.invoke({"query": prompt})
                    answer = response["result"]
                    response_placeholder.markdown(answer)
                    
                    # Convert document metadata arrays to JSON-serializable structures for history persistence
                    serialized_sources = []
                    sources = response.get("source_documents", [])
                    for doc in sources:
                        serialized_sources.append({
                            "source": doc.metadata.get("source", "Unknown"),
                            "file": doc.metadata.get("file", "Unknown"),
                            "content": doc.page_content[:300].replace("\n", " ") + "..."
                        })
                    
                    if serialized_sources:
                        with st.expander("🔍 Explored Context Sources"):
                            for doc in serialized_sources:
                                if doc["source"] == "KB":
                                    st.markdown(f'<div class="source-card-kb"><strong>Corporate Policy Document:</strong><br/>{doc["content"]}</div>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<div class="source-card-user"><strong>File: {doc["file"]}</strong><br/>{doc["content"]}</div>', unsafe_allow_html=True)
        
        # Save complete trace to history
        st.session_state.chat_history.append(("user", prompt))
        st.session_state.chat_history.append(("assistant", answer, serialized_sources))
    else:
        st.sidebar.warning("Please upload application structural data files to drop into execution mode.")