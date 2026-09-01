import os
import logging
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import httpx
from dotenv import load_dotenv

load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mistral-service")

app = FastAPI(
    title="Mistral AI Render API",
    description="FastAPI backend to serve Mistral AI model or proxy to local/cloud LLM endpoints for Chatbots.",
    version="1.0.0"
)

# Enable CORS for chatbot frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment configuration
ENGINE_MODE = os.getenv("ENGINE_MODE", "proxy").lower()  # Options: 'llama_cpp', 'remote_ollama', 'mistral_api', 'proxy'
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")
MODEL_REPO = os.getenv("MODEL_REPO", "TheBloke/Mistral-7B-Instruct-v0.2-GGUF")
MODEL_FILE = os.getenv("MODEL_FILE", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")

# Global LLM instance container for llama_cpp
llm_instance = None

if ENGINE_MODE == "llama_cpp":
    try:
        from llama_cpp import Llama
        logger.info(f"Initializing Llama C++ model from HF repo: {MODEL_REPO}, file: {MODEL_FILE}")
        llm_instance = Llama.from_pretrained(
            repo_id=MODEL_REPO,
            filename=MODEL_FILE,
            n_ctx=2048,
            n_threads=int(os.getenv("N_THREADS", "4"))
        )
        logger.info("Llama C++ model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load llama_cpp model: {e}")
        llm_instance = None

class Message(BaseModel):
    role: str = Field(..., description="Role of the message author: 'system', 'user', or 'assistant'")
    content: str = Field(..., description="Message text content")

class ChatCompletionRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = "mistral-7b-instruct"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512
    stream: Optional[bool] = False

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Mistral AI Chatbot API",
        "engine_mode": ENGINE_MODE,
        "docs": "/docs",
        "endpoints": ["/health", "/api/chat", "/v1/chat/completions"]
    }

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "engine_mode": ENGINE_MODE,
        "model_loaded": llm_instance is not None if ENGINE_MODE == "llama_cpp" else True,
        "ollama_url": OLLAMA_BASE_URL if ENGINE_MODE == "remote_ollama" else None
    }

@app.post("/api/chat")
@app.post("/v1/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    """
    Unified chat completions endpoint. Supports llama_cpp self-hosting, 
    remote Ollama tunneling, and official Mistral API proxying.
    """
    formatted_messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

    # --- Mode 1: Self-Hosted Llama C++ (Local / Render CPU) ---
    if ENGINE_MODE == "llama_cpp":
        if not llm_instance:
            raise HTTPException(
                status_code=503,
                detail="Llama C++ model is not loaded. Check server logs or memory allocation."
            )
        try:
            response = llm_instance.create_chat_completion(
                messages=formatted_messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            return response
        except Exception as e:
            logger.error(f"Llama C++ execution error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # --- Mode 2: Remote Ollama (Local tunnel via Ngrok / Cloudflare) ---
    elif ENGINE_MODE == "remote_ollama":
        target_url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"
        payload = {
            "model": request.model or "mistral",
            "messages": formatted_messages,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(target_url, json=payload)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                
                ollama_data = resp.json()
                assistant_message = ollama_data.get("message", {}).get("content", "")
                
                return {
                    "id": "chatcmpl-ollama",
                    "object": "chat.completion",
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": assistant_message
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
        except httpx.RequestError as exc:
            logger.error(f"Ollama connection error: {exc}")
            raise HTTPException(status_code=502, detail=f"Failed to connect to Ollama endpoint at {OLLAMA_BASE_URL}: {exc}")

    # --- Mode 3: Official Mistral API Proxy ---
    elif ENGINE_MODE in ["mistral_api", "proxy"]:
        if not MISTRAL_API_KEY:
            raise HTTPException(
                status_code=401,
                detail="MISTRAL_API_KEY is not configured on the server environment."
            )
        target_url = "https://api.mistral.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MISTRAL_MODEL,
            "messages": formatted_messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(target_url, headers=headers, json=payload)
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                return resp.json()
        except httpx.RequestError as exc:
            logger.error(f"Mistral API request error: {exc}")
            raise HTTPException(status_code=502, detail=f"Failed to connect to Mistral API: {exc}")

    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown ENGINE_MODE: '{ENGINE_MODE}'. Supported: 'llama_cpp', 'remote_ollama', 'mistral_api'."
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
