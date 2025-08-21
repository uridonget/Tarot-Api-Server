import os
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

TAROT_PROMPT_TEMPLATE = """
# 역할
당신은 따뜻하고 지혜로운 타로 마스터입니다.

# 지침
- 사용자의 사연과 뽑힌 카드를 바탕으로, '과거', '현재', '미래'에 대한 해석과 '총평'을 담은 JSON 객체를 생성해주세요.
- JSON의 각 값은 해당 카드와 상황에 대한 구체적인 해석이어야 합니다.
- 각 해석은 최소 1~2문장으로 구성해주세요.
- 전체 해석의 총 길이는 150자 이상, 300자 이하로 작성해주세요.

# 타로점 정보
- 방식: {method}
- 규칙: {rule}
- 뽑힌 카드: {cards}

# 사용자의 사연
- 고민: {story}

# 출력 형식 (반드시 이 JSON 구조만 반환해야 합니다. 다른 텍스트는 포함하지 마세요.)
{output_format}
"""


def get_tarot_reading(
    method: str, rule: str, cards: str, story: str, output_format: str
) -> dict:
    prompt = TAROT_PROMPT_TEMPLATE.format(
        method=method, rule=rule, cards=cards, story=story, output_format=output_format
    )
    try:
        response = model.generate_content(prompt)
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON from the model's response."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {e}"}
