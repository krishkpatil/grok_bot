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
    Renders 'chat.html', which includes text input, file upload, and send buttons.
    """
    return render(request, "chat.html")

@csrf_exempt
def upload_file(request):
    """
    Handles file uploads and returns the extracted content.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=400)

    uploaded_file = request.FILES.get("file")
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded."}, status=400)

    try:
        # Check file type and process accordingly
        if uploaded_file.name.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            content = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
        else:
            return JsonResponse({"error": "Unsupported file type. Please upload .txt or .pdf files."}, status=400)

        return JsonResponse({"content": content})
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return JsonResponse({"error": f"Error processing file: {e}"}, status=500)

@csrf_exempt
def send_message(request):
    """
    Handles chatbot interaction:
    1) Accepts POST with a "message" field from the user.
    2) Optionally combines extracted file content (if uploaded).
    3) Sends it to x.ai's Grok (OpenAI-compatible endpoint).
    4) Returns {"reply": "..."} as JSON.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=400)

    user_message = request.POST.get("message", "").strip()
    uploaded_file = request.FILES.get("file")
    extracted_text = ""

    # Handle file content extraction
    if uploaded_file:
        try:
            if uploaded_file.name.endswith(".txt"):
                extracted_text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.name.endswith(".pdf"):
                reader = PdfReader(uploaded_file)
                extracted_text = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
            else:
                return JsonResponse({"error": "Unsupported file type. Please upload .txt or .pdf files."}, status=400)
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return JsonResponse({"error": f"Error processing file: {e}"}, status=500)

    if not user_message and not extracted_text:
        return JsonResponse({"error": "No message or file content provided."}, status=400)

    if OpenAI is None:
        return JsonResponse({"error": "OpenAI library not installed or import failed"}, status=500)

    # Combine extracted file content with user message
    combined_message = user_message
    if extracted_text:
        combined_message += f"\n\n[Extracted File Content]:\n{extracted_text}"

    # Initialize the OpenAI client for x.ai
    client = OpenAI(
        api_key=settings.XAI_API_KEY,
        base_url="https://api.x.ai/v1",
    )

    try:
        # Prepare conversation for OpenAI-compatible API
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that reads information provided and generates responses or scripts when prompted."
            },
            {"role": "user", "content": combined_message},
        ]

        # Make the request to the chatbot API
        completion = client.chat.completions.create(
            model="grok-beta",
            messages=messages,
            stream=False,
            temperature=0.7,
        )

        # Debug log for API response
        logger.debug("Raw x.ai response: %s", completion)
        print("DEBUG raw x.ai response:", completion)

        # Extract reply from API response
        if completion.choices and len(completion.choices) > 0:
            grok_reply = completion.choices[0].message.content
        else:
            grok_reply = "[No valid reply in response]"

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error: {req_err}")
        grok_reply = f"Network/HTTP error: {req_err}"
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        grok_reply = f"Error reaching x.ai Grok: {e}"

    return JsonResponse({"reply": grok_reply})
