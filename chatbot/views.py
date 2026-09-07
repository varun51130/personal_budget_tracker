import os
import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

# Load .env once at startup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Correctly read the GEMINI API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def chat_page(request):
    """Render the chatbot HTML page"""
    return render(request, "chatbot/chat.html")


@csrf_exempt
@require_POST
def chat_api(request):
    """Handle AJAX POST requests to Gemini API"""
    try:
        # Parse incoming JSON
        data = json.loads(request.body.decode("utf-8"))
        message = data.get("message", "").strip()

        if not message:
            return JsonResponse({"reply": "Please enter a message."})

        if not GEMINI_API_KEY:
            return JsonResponse({"error": "GEMINI_API_KEY not set"}, status=500)

        # Gemini API endpoint (current generateContent format)
        GEMINI_MODEL = "gemini-2.5-flash"
        GEMINI_URL = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        )

        # Request payload (current Gemini generateContent format)
        payload = {
            "contents": [
                {"parts": [{"text": message}]}
            ],
            "generationConfig": {"temperature": 0.7, "candidateCount": 1},
        }

        # API key is sent via header, not the URL, so it never ends up in logs/error messages
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY,
        }

        # Send request to Gemini API
        response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        resp_json = response.json()

        # Safely extract the reply
        candidates = resp_json.get("candidates", [])
        reply = "No response from Gemini API"
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts and "text" in parts[0]:
                reply = parts[0]["text"]

        return JsonResponse({"reply": reply})

    except requests.exceptions.RequestException as e:
        return JsonResponse(
            {"error": "Failed to contact Gemini API", "details": str(e)}, status=500
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON received"}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Unexpected error", "details": str(e)}, status=500)
