import json
import random
import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.request import get_tarot_reading
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

app = FastAPI()

with open("app/tarot_config.json", "r", encoding="utf-8") as f:
    tarot_configs = json.load(f)

with open("app/tarot_cards.json", "r", encoding="utf-8") as f:
    tarot_cards_data = json.load(f)["cards"]

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    raise ValueError("SLACK_BOT_TOKEN environment variable not set")
slack_client = WebClient(token=SLACK_BOT_TOKEN)


class TarotReadingRequest(BaseModel):
    story: str
    config_key: str  # e.g., "one_card", "three_card", "five_card"


def get_random_tarot_card():
    """Draws a single random tarot card."""
    card = random.choice(tarot_cards_data)
    orientation = random.choice(["정방향", "역방향"])
    meaning = card["upright"] if orientation == "정방향" else card["reversed"]
    return {
        "card_name": card["name"],
        "orientation": orientation,
        "meaning": meaning,
    }


def _generate_tarot_reading(story: str, config_key: str):
    """Generates a tarot reading based on a story and config key."""
    if config_key not in tarot_configs:
        raise ValueError("Invalid config_key")

    config = tarot_configs[config_key]
    num_cards = int(config["method"].split(" ")[0])
    drawn_cards = [get_random_tarot_card() for _ in range(num_cards)]
    cards_str = ", ".join(
        [f'{c["card_name"]} ({c["orientation"]})' for c in drawn_cards]
    )

    reading = get_tarot_reading(
        method=config["method"],
        rule=config["rule"],
        cards=cards_str,
        story=story,
        output_format=config["output_format"],
    )
    return {"reading": reading, "cards": drawn_cards}


def format_reading_for_slack(result: dict) -> str:
    cards = result.get("cards", [])
    reading = result.get("reading", {})

    cards_info = "\n".join(
        [f"- *{c['card_name']} ({c['orientation']})*: {c['meaning']}" for c in cards]
    )

    reading_parts = []
    if isinstance(reading, dict):
        for key, value in reading.items():
            reading_parts.append(f"*{key.capitalize()}*: {value}")

    reading_info = "\n".join(reading_parts)

    return f"""
:crystal_ball: *당신의 타로점 결과입니다* :crystal_ball:

*뽑은 카드:*
{cards_info}

*해석:*
{reading_info}
"""


@app.get("/")
def health_check():
    return {"status": "ok"}


@app.post("/tarot")
def create_tarot_reading_api(request: TarotReadingRequest):
    try:
        result = _generate_tarot_reading(request.story, request.config_key)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tarot reading: {e}")


@app.post("/slack/events")
async def slack_events(request: Request):
    body = await request.json()

    # Slack URL Verification Challenge
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    # Handle actual events
    event = body.get("event", {})
    if event.get("type") == "app_mention":
        # Avoid responding to the bot's own messages
        if event.get("bot_id"):
            return {"status": "ok"}

        channel_id = event.get("channel")
        user_text = event.get("text", "").split(">", 1)[-1].strip()

        try:
            # Use a default reading type for Slack, e.g., "three_card"
            result = _generate_tarot_reading(story=user_text, config_key="three_card")

            # Format and send the message to Slack
            slack_message = format_reading_for_slack(result)
            slack_client.chat_postMessage(channel=channel_id, text=slack_message)

        except Exception as e:
            # Notify user in case of an error
            error_message = f"죄송합니다, 타로점을 보는 중 오류가 발생했어요: {e}"
            slack_client.chat_postMessage(channel=channel_id, text=error_message)

    return {"status": "ok"}
