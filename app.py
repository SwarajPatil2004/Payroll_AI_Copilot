from fastapi import FastAPI
from config import APP_NAME
from models import ChatRequest, ChatResponse
from copilot import PayrollCopilot

app = FastAPI(title=APP_NAME)

copilot = PayrollCopilot()


# @app.get("/health")
# def health():

#     return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    return copilot.chat(req)
