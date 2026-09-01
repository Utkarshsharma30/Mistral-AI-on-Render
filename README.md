# Deploying Mistral AI Backend to Render

This project provides a production-ready **FastAPI** web service designed to serve or proxy **Mistral AI** models for your chatbot application. It comes ready for **1-click deployment on Render.com** via Docker.

---

## 🌟 Features

- **Multi-Engine Support**: Easily switch between:
  1. `llama_cpp`: Self-host quantized GGUF models directly on Render CPU.
  2. `remote_ollama`: Tunnel your local PC's Ollama model to Render using Ngrok or Cloudflare.
  3. `proxy` / `mistral_api`: Proxy requests through Render to official cloud APIs.
- **CORS Enabled**: Out-of-the-box support for React, Vue, Next.js, HTML/JS, or mobile chatbot apps.
- **OpenAI-Compatible Spec**: Uses standard `/v1/chat/completions` and `/api/chat` endpoints.
- **Render Ready**: Includes `Dockerfile` and `render.yaml` blueprint.

---

## 🚀 Step 1: Deploy to Render.com

### Option A: Automatic Blueprint Deployment (Recommended)
1. Push this folder (`d:\Render AI locally`) to a new repository on **GitHub** or **GitLab**.
2. Log into [Render Dashboard](https://dashboard.render.com).
3. Click **New +** -> **Blueprint**.
4. Connect your repository. Render will automatically read `render.yaml` and configure the Web Service.

### Option B: Manual Web Service Setup
1. Log into [Render Dashboard](https://dashboard.render.com).
2. Click **New +** -> **Web Service**.
3. Select **Build and deploy from a Git repository**.
4. Choose **Docker** as the Runtime environment.
5. In **Environment Variables**, configure the key-value pairs described below.

---

## ⚙️ Environment Variable Settings on Render

In the Render Dashboard under **Environment**, set the following depending on your preferred mode:

### Mode 1: Run Model Directly on Render (`ENGINE_MODE = llama_cpp`)
> *Requires Render Starter (2GB RAM) or Standard (8GB RAM) plan.*
- `ENGINE_MODE`: `llama_cpp`
- `MODEL_REPO`: `TheBloke/Mistral-7B-Instruct-v0.2-GGUF`
- `MODEL_FILE`: `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (or a smaller 1B-3B model like `qwen1.5-1.8b-chat.Q4_K_M.gguf`)

### Mode 2: Expose Your Local Ollama Model (`ENGINE_MODE = remote_ollama`)
> *Free Tier friendly! Runs the heavy AI model on your local PC GPU/CPU, and uses Render for your chatbot's public HTTPS URL.*
1. Start your local Ollama / Mistral model on your PC (`ollama run mistral`).
2. Run Ngrok or Cloudflare Tunnel on your local machine:
   ```bash
   ngrok http 11434
   ```
3. Set environment variables on Render:
   - `ENGINE_MODE`: `remote_ollama`
   - `OLLAMA_BASE_URL`: `https://<your-ngrok-subdomain>.ngrok-free.app`

### Mode 3: Proxy via API Key (`ENGINE_MODE = proxy`)
> *Free Tier friendly! Uses Render to protect your API keys and enforce CORS.*
- `ENGINE_MODE`: `proxy`
- `MISTRAL_API_KEY`: `your_mistral_api_key_here`
- `MISTRAL_MODEL`: `mistral-tiny`

---

## 🧪 Testing Your Render Endpoint

Once deployed, Render provides a public HTTPS URL (e.g. `https://mistral-chatbot-api.onrender.com`).

### 1. Test Health Endpoint
```bash
curl https://mistral-chatbot-api.onrender.com/health
```

### 2. Test Chat Endpoint with `curl`
```bash
curl -X POST "https://mistral-chatbot-api.onrender.com/api/chat" \
     -H "Content-Type: application/json" \
     -d '{
       "messages": [
         {"role": "system", "content": "You are a helpful chatbot."},
         {"role": "user", "content": "Hello!"}
       ]
     }'
```

### 3. Test using Python
```bash
python test_api.py https://mistral-chatbot-api.onrender.com
```

---

## 💻 Frontend Chatbot Integration Example (JavaScript)

```javascript
async function sendChatMessage(userText) {
  const response = await fetch("https://mistral-chatbot-api.onrender.com/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: userText }
      ],
      temperature: 0.7
    })
  });

  const data = await response.json();
  const botReply = data.choices[0].message.content;
  console.log("Bot:", botReply);
  return botReply;
}
```
