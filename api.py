from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi import FastAPI
from google.genai import types
from typing import Literal

load_dotenv()

client = genai.Client()
app = FastAPI()


class Review(BaseModel):
    text: str


class Analysis(BaseModel):
    label: str
    score: int 
    theme: str


@app.get("/reviews")
def get_reviews():
    return {
        "message": "Here are the reviews",
        "reviews": [
            "The food was amazing!",
            "Delivery was very late.",
            "Good quality for the price."
        ]
    }


@app.post("/analyze")
def analyze(review: Review):

    response = client.models.generate_content(
        model="gemini-3.7-flash",
        contents=f'''
Analyze the customer review.

label must be "positive", "negative", or "neutral".
score must be an integer between 1 (very bad) and 5 (very good).
theme must be a single lowercase word representing the main topic
of the review (for example: service, delivery, quality, taste, price).

Review: {review.text}
''',
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=Analysis,
        ),
    )

    return response.parsed

