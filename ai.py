from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

g_api = os.getenv("GEMINI_API")

client = genai.Client(api_key=g_api)

MODEL_NAME = "gemini-3.6-flash"

def has_key():
    return client is not None

def _generate(prompt, fallback):
    if client is None:
        return fallback
    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        return (response.text or "").strip() or fallback
    except Exception as exc:  # noqa: BLE001 - never let AI text break a page
        print(f"Gemini call failed: {exc}")
        return fallback


def get_recipe_summary(recipes):
    summaries = []
    for recipe in recipes:
        prompt = (f"Based on this recipe: {recipe}, give me a 3-sentence "
                  "description of the recipe and why it is healthy for someone.")
        summaries.append(_generate(prompt, fallback="Summary unavailable right now."))
    return summaries


def get_score_explanation(title, nutrient_totals, score, breakdown):
    prompt = (
        f"The recipe '{title}' scored {score}/100 for how well one serving fits "
        f"a person's daily nutrition targets. One serving has: {nutrient_totals}. "
        f"Factor ratings: {breakdown}. In two short, friendly, non-judgmental "
        "sentences, explain roughly why it scored this way. Do not invent a "
        "different score and do not give medical advice."
    )
    return _generate(
        prompt,
        fallback=(f"This meal scored {score}/100 based on how one serving "
                  "compares with your daily targets."),
    )