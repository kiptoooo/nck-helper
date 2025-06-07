from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os, glob, requests

# LangChain imports
from langchain.document_loaders import JSONLoader, TextLoader, PyPDFLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str

# Config
TOGETHER_KEY = os.getenv("TOGETHER_API_KEY")
MODEL = "togethercomputer/llama-3-70b-chat"

if not TOGETHER_KEY:
    raise RuntimeError("Missing TOGETHER_API_KEY environment variable")

# Initialize embeddings
emb = OpenAIEmbeddings(openai_api_key=TOGETHER_KEY)

# Load FAQs
faq_loader = JSONLoader("knowledge/faqs.json", jq_schema=".[]")
faq_docs = faq_loader.load()

# Load manuals (.txt and .pdf)
manual_docs = []
for path in glob.glob("knowledge/manuals/*"):
    if path.lower().endswith(".txt"):
        manual_docs.extend(TextLoader(path).load())
    elif path.lower().endswith(".pdf"):
        manual_docs.extend(PyPDFLoader(path).load())

# Combine and build vectorstore
docs = faq_docs + manual_docs
vectordb = Chroma.from_documents(docs, emb, persist_directory="./chroma_db")
qa_chain = RetrievalQA.from_chain_type(
    llm=lambda **kwargs: requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {TOGETHER_KEY}"},
        json={"model": MODEL, **kwargs}
    ).json()["choices"][0]["message"],
    chain_type="stuff",
    retriever=vectordb.as_retriever(search_kwargs={"k":5})
)

@app.post("/chat")
async def chat(req: ChatRequest):
    answer = qa_chain.run(req.message)
    return JSONResponse({"reply": answer})

@app.get("/", response_class=HTMLResponse)
def root():
    return open("static/index.html").read()