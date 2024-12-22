import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render

# Attempt to import the OpenAI wrapper that x.ai says can be adapted.
# If you haven't installed openai, run: pip install openai
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

def chat_page(request):
    """
    Renders 'chat.html', which has a text input and a 'Send' button
    that POSTs a message to '/chat/send'.
    """
    return render(request, "chat.html")

@csrf_exempt
def send_message(request):
    """
    1) Accepts POST with a "message" field from the user.
    2) Sends it to x.ai's Grok (OpenAI-compatible endpoint).
    3) Returns {"reply": "..."} as JSON.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=400)

    user_message = request.POST.get("message", "").strip()
    if not user_message:
        return JsonResponse({"error": "No message provided"}, status=400)

    if OpenAI is None:
        return JsonResponse({"error": "OpenAI library not installed"}, status=500)

    # Initialize the OpenAI client for x.ai
    client = OpenAI(
        api_key=settings.XAI_API_KEY,     # x.ai API key from settings.py
        base_url="https://api.x.ai/v1",   # x.ai's OpenAI-compatible endpoint
    )

    try:
        # Build the conversation
        messages = [
            {"role": "system", "content": "You are a test assistant."},
            {"role": "user", "content": user_message}
        ]

        # Make the request to x.ai
        completion = client.chat.completions.create(
            model="grok-beta",  # or whichever model your cURL tests show works
            messages=messages,
            stream=False,
            temperature=0,
        )

        # Debug: Log the entire response
        logger.debug("Raw x.ai response: %s", completion)
        print("DEBUG raw x.ai response:", completion)

        # If you want to use the object's attributes directly:
        if completion.choices and len(completion.choices) > 0:
            grok_reply = completion.choices[0].message.content
        else:
            grok_reply = "[No valid reply in response]"


    except requests.exceptions.RequestException as req_err:
        grok_reply = f"Network/HTTP error: {req_err}"
    except Exception as e:
        grok_reply = f"Error reaching x.ai Grok: {e}"

    return JsonResponse({"reply": grok_reply})
