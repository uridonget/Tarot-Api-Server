import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.request import get_tarot_reading

app = FastAPI()

# Load tarot configurations from JSON file
with open("app/tarot_config.json", "r", encoding="utf-8") as f:
    tarot_configs = json.load(f)


class TarotReadingRequest(BaseModel):
    cards: str
    story: str
    config_key: str  # e.g., "one_card", "three_card", "five_card"


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/tarot")
def create_tarot_reading(request: TarotReadingRequest):
    if request.config_key not in tarot_configs:
        raise HTTPException(status_code=400, detail="Invalid config_key")

    config = tarot_configs[request.config_key]

    try:
        reading = get_tarot_reading(
            method=config["method"],
            rule=config["rule"],
            cards=request.cards,
            story=request.story,
            output_format=config["output_format"],
        )
        return reading
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tarot reading: {e}")
