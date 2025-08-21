import json
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.request import get_tarot_reading

app = FastAPI()

# Load tarot configurations from JSON file
with open("app/tarot_config.json", "r", encoding="utf-8") as f:
    tarot_configs = json.load(f)

# Load tarot card data from JSON file
with open("app/tarot_cards.json", "r", encoding="utf-8") as f:
    tarot_cards_data = json.load(f)["cards"]


class TarotReadingRequest(BaseModel):
    story: str
    config_key: str  # e.g., "one_card", "three_card", "five_card"


@app.get("/")
def health_check():
    return {"status": "ok"}


def get_random_tarot_card():
    """
    Draws a single random tarot card, determining if it's upright or reversed.
    """
    # Select a random card from the deck
    card = random.choice(tarot_cards_data)

    # Determine the orientation (upright or reversed)
    orientation = random.choice(["정방향", "역방향"])

    # Select the meaning based on the orientation
    if orientation == "정방향":
        meaning = card["upright"]
    else:
        meaning = card["reversed"]

    return {
        "card_name": card["name"],
        "orientation": orientation,
        "meaning": meaning,
    }


@app.post("/tarot")
def create_tarot_reading(request: TarotReadingRequest):
    if request.config_key not in tarot_configs:
        raise HTTPException(status_code=400, detail="Invalid config_key")

    config = tarot_configs[request.config_key]

    # Determine the number of cards to draw
    method = config["method"]
    num_cards = int(method.split(" ")[0])

    # Draw random cards
    drawn_cards = [get_random_tarot_card() for _ in range(num_cards)]

    # Format cards for the prompt
    cards_str = ", ".join(
        [f'{card["card_name"]} ({card["orientation"]})' for card in drawn_cards]
    )

    try:
        reading = get_tarot_reading(
            method=config["method"],
            rule=config["rule"],
            cards=cards_str,
            story=request.story,
            output_format=config["output_format"],
        )
        return {"reading": reading, "cards": drawn_cards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tarot reading: {e}")
