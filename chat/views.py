import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from PyPDF2 import PdfReader

# Attempt to import the OpenAI wrapper that x.ai says can be adapted.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

def chat_page(request):
    """
    Renders 'chat.html', which has a text input, a file upload button, and a 'Send' button.
    """
    return render(request, "chat.html")


@csrf_exempt
def upload_file(request):
    """
    Handle file uploads (e.g., .txt, .pdf).
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=400)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded."}, status=400)

    # Check file type
    if uploaded_file.name.endswith(".txt"):
        # Read .txt file
        try:
            content = uploaded_file.read().decode("utf-8")
            return JsonResponse({"content": content})
        except Exception as e:
            return JsonResponse({"error": f"Error reading text file: {e}"})
    elif uploaded_file.name.endswith(".pdf"):
        # Parse PDF (requires PyPDF2)
        try:
            reader = PdfReader(uploaded_file)
            content = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
            return JsonResponse({"content": content})
        except Exception as e:
            return JsonResponse({"error": f"Error parsing PDF: {e}"})
    else:
        return JsonResponse({"error": "Unsupported file type."}, status=400)


@csrf_exempt
def send_message(request):
    """
    Handles chatbot interaction:
    1) Accepts POST with a "message" field from the user.
    2) Optionally combines file content (if uploaded).
    3) Sends it to x.ai's Grok (OpenAI-compatible endpoint).
    4) Returns {"reply": "..."} as JSON.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=400)

    user_message = request.POST.get("message", "").strip()
    uploaded_file = request.FILES.get("file")
    extracted_text = ""

    # Extract file content if provided
    if uploaded_file:
        if uploaded_file.name.endswith(".txt"):
            try:
                extracted_text = uploaded_file.read().decode("utf-8")
            except Exception as e:
                return JsonResponse({"error": f"Error reading text file: {e}"})
        elif uploaded_file.name.endswith(".pdf"):
            try:
                reader = PdfReader(uploaded_file)
                extracted_text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
            except Exception as e:
                return JsonResponse({"error": f"Error parsing PDF: {e}"})
        else:
            return JsonResponse({"error": "Unsupported file type."}, status=400)

    if not user_message and not extracted_text:
        return JsonResponse({"error": "No message or file provided"}, status=400)

    if OpenAI is None:
        return JsonResponse({"error": "OpenAI library not installed"}, status=500)

    # Combine the extracted text with the user message
    combined_message = user_message
    if extracted_text:
        combined_message += f"\n\nExtracted text:\n{extracted_text}"

    # Initialize the OpenAI client for x.ai
    client = OpenAI(
        api_key=settings.XAI_API_KEY,     # x.ai API key from settings.py
        base_url="https://api.x.ai/v1",   # x.ai's OpenAI-compatible endpoint
    )

    try:
        # Build the conversation
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": combined_message}
        ]

        # Make the request to x.ai
        completion = client.chat.completions.create(
            model="grok-beta",
            messages=messages,
            stream=False,
            temperature=0,
        )

        # Debug: Log the entire response
        logger.debug("Raw x.ai response: %s", completion)
        print("DEBUG raw x.ai response:", completion)

        # Extract the bot's reply
        if completion.choices and len(completion.choices) > 0:
            grok_reply = completion.choices[0].message.content
        else:
            grok_reply = "[No valid reply in response]"

    except requests.exceptions.RequestException as req_err:
        grok_reply = f"Network/HTTP error: {req_err}"
    except Exception as e:
        grok_reply = f"Error reaching x.ai Grok: {e}"

    return JsonResponse({"reply": grok_reply})
