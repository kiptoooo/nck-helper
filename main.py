from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from langchain.document_loaders import JSONLoader, TextLoader, PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import os

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load knowledge base
faq_loader = JSONLoader("knowledge/faqs.json")
text_loaders = []
for file in os.listdir("knowledge/manuals"):
    path = os.path.join("knowledge/manuals", file)
    if file.endswith('.txt'):
        text_loaders.append(TextLoader(path))
    elif file.endswith('.pdf'):
        text_loaders.append(PyPDFLoader(path))

docs = faq_loader.load() + [l.load() for l in text_loaders]

# Build vector store for RAG
embeddings = HuggingFaceEmbeddings()
vectordb = Chroma.from_documents(docs, embeddings)
qa_chain = RetrievalQA.from_chain_type(
    ChatOpenAI(model_name="gpt-3.5-turbo"),
    retriever=vectordb.as_retriever()
)

@app.get("/", response_class=HTMLResponse)
def index():
    with open("static/index.html") as f:
        return f.read()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_question = data.get("message")
    answer = qa_chain.run(user_question)
    return {"reply": answer}