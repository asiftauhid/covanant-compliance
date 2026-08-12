import time
from contextlib import asynccontextmanager
from typing import Literal

import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"

tokenizer = None
model = None


class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class GenerateRequest(BaseModel):
    messages: list[Message]
    max_tokens: int = Field(default=512, ge=1, le=2048)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class GenerateResponse(BaseModel):
    text: str
    model: str
    inference_ms: int
    device: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tokenizer, model
    print(f"Loading {MODEL_ID} on CPU...")
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.float32,
        device_map="cpu",
    )
    model.eval()
    print("Model loaded.")
    yield


app = FastAPI(title="Covenant LLM Service", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_ID,
        "loaded": model is not None,
        "device": "cpu",
    }


@app.post("/v1/chat", response_model=GenerateResponse)
def chat(request: GenerateRequest):
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    start = time.perf_counter()

    messages = [m.model_dump() for m in request.messages]
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(prompt, return_tensors="pt")

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            do_sample=request.temperature > 0,
            temperature=request.temperature if request.temperature > 0 else None,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated = output[0][inputs["input_ids"].shape[-1] :]
    text = tokenizer.decode(generated, skip_special_tokens=True).strip()
    inference_ms = int((time.perf_counter() - start) * 1000)

    return GenerateResponse(
        text=text,
        model=MODEL_ID,
        inference_ms=inference_ms,
        device="cpu",
    )
