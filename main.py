import json
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

AI_PIPE_MODEL = "openai/gpt-4.1"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"]
)

def coerce(value, typ):
    if value is None:
        return None
    try:
        t = str(typ).lower().strip()
        if t == "integer":
            return int(round(float(str(value).replace(",", ""))))
        if t in ("float", "number"):
            return float(str(value).replace(",", ""))
        if t == "boolean":
            if isinstance(value, bool):
                return value
            return str(value).strip().lower() in ("true", "1", "yes", "y")
        if t == "date":
            return str(value).strip()
        if t == "array[integer]":
            lst = value if isinstance(value, list) else [value]
            return [int(round(float(x))) for x in lst]
        if t.startswith("array"):
            lst = value if isinstance(value, list) else [value]
            return [str(x).strip().rstrip(".").strip() if isinstance(x, str) else x for x in lst]
        return str(value).strip().rstrip(".").strip()
    except Exception:
        return None

@app.post("/dynamic-extract")
async def dynamic_extract(request: Request):
    token = os.getenv("AIPIPE_TOKEN")
    body = await request.json()
    text = body.get("text", "")
    schema = body.get("schema", {})
    keys = list(schema.keys())

    prompt = (
        "Extract variables from the text. Return JSON with EXACTLY these keys:\n"
        f"{json.dumps(schema, indent=2)}\n\n"
        "Rules: dates -> ISO YYYY-MM-DD; integer/float -> JSON numbers; boolean -> true/false; array[...] -> JSON array;"
        "for string fields, copy the exact text span from the source with no paraphrasing, no articles, and no punctuation changes;"
        "remove any stop wards from the string"
        "if a field cannot be found use null.\n\n"
        f"TEXT:\n{text}"
    )

    payload = {
        "model": AI_PIPE_MODEL,
        "input": prompt,
        "temperature": 0
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://aipipe.org/openrouter/v1/responses",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            data = data["output"][0]["content"][0]["text"]
            data = json.loads(data)
            return {key: coerce(data.get(key, None), schema[key]) for key in keys}
    except Exception as error:
        print(error)
        return {}

@app.get("/")
def health_check():
    return {"status": "ok"}
