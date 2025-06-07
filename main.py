import os
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

# --- config ----
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
TOGETHER_MODEL = "togethercomputer/llama-3-70b-chat"

# build a simple Chroma index over your docs/faqs
# (you can preload on startup)
embedding = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))
store = Chroma.from_documents(
    documents=[
        # load your faqs.json as simple docs
        *[
            {"page_content": f"{qa['q']}\nA: {qa['a']}"}
            for qa in json.load(open("knowledge/faqs.json"))
        ],
        # load all .txt in manuals/
        *[
            {"page_content": open(f"knowledge/manuals/{fn}").read()}
            for fn in os.listdir("knowledge/manuals")
            if fn.endswith(".txt")
        ],
    ],
    embedding=embedding,
    persist_directory="chromadb"
)
qa_chain = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo"),
    retriever=store.as_retriever(),
)

app = FastAPI()

# serve your static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat(req: ChatRequest):
    user_q = req.message

    # first fetch relevant context
    context = qa_chain.run(user_q)

    # then call Together.ai with context + question
    hdr = {"Authorization": f"Bearer {TOGETHER_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": TOGETHER_MODEL,
        "messages": [
            {"role": "system", "content": "You are Medical Assistant specialized in nursing licensing prep."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_q}"}
        ]
    }
    resp = requests.post("https://api.together.xyz/v1/chat/completions", headers=hdr, json=payload)
    if resp.status_code != 200:
        raise HTTPException(502, detail="Together.ai error")
    ans = resp.json()["choices"][0]["message"]["content"]
    return {"reply": ans}

@app.get("/")
def index():
    return FileResponse("static/index.html")
