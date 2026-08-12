---
title: Covenant LLM
emoji: 📊
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# Covenant LLM Service

Self-hosted **Qwen2.5-1.5B-Instruct** on Hugging Face Spaces (CPU).

Open-source model — no OpenAI or public inference API. Data stays on your Space.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Model load status |
| POST | `/v1/chat` | Chat completion |

### Example

```bash
curl -X POST https://YOUR-USERNAME-covenant-llm.hf.space/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Say hello in one sentence."}
    ],
    "max_tokens": 64,
    "temperature": 0.1
  }'
```

## Deploy to Hugging Face

1. Create a new **Space** → SDK: **Docker**
2. Push this `llm-service/` folder (or link repo subdirectory)
3. Space builds and downloads Qwen on first start (~3–5 min)
4. Copy the Space URL into your main app's `.env`:

```env
LLM_PROVIDER=hf_space
LLM_BASE_URL=https://YOUR-USERNAME-covenant-llm.hf.space
```

> **Note:** As of 2026, creating Docker Spaces may require [HF PRO](https://huggingface.co/pricing). CPU Basic hardware is free once the Space exists.

## Local test (before deploy)

```bash
cd llm-service
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

First run downloads ~3GB model weights.
