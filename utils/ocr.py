import anthropic
import requests
import os
import base64
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# 🔍 OCR Setup
# ─────────────────────────────────────────────


def run_ocr_on_url(file_url: str) -> str:
    """Downloads image from Telegram and extracts handwritten text using Claude Vision."""
    claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Download image
    response = requests.get(file_url)
    image_data = base64.standard_b64encode(response.content).decode("utf-8")

    # Send to Claude Vision
    message = claude_client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "This is a page of handwritten notes in French about Brazilian Jiu-Jitsu (BJJ), "
                            "specifically nogi (no-gi) grappling. "
                            "The notes may contain French words mixed with English BJJ/grappling terminology, "
                            "abbreviations, position names (garde, demi-garde, dos, turtle, x-guard...), "
                            "submission names (étranglement, clé de bras, heel hook, kimura...), "
                            "and technical concepts (passage de garde, takedown, sweep, scramble...). \n\n"
                            "Please transcribe ALL the text exactly as written, "
                            "preserving the original line breaks, structure, bullet points and indentation. "
                            "If a word is ambiguous, use your BJJ knowledge to pick the most likely term. "
                            "Return only the transcribed text, nothing else."
                        )
                    }
                ],
            }
        ],
    )
    
    return message.content[0].text or "No text found."