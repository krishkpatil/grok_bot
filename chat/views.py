import logging
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
from PyPDF2 import PdfReader
from .models import Chat
import json
import os
from django.utils.timezone import now
from django.utils.timesince import timesince

def chat_page(request):
    """
    Renders 'chat.html', which includes text input, file upload, and send buttons,
    along with a list of previous chats.
    """
    chats = Chat.objects.all().order_by('-created_at')  # Fetch all chats
    chat_data = [
        {
            "message": chat.message,
            "response": chat.response,
            "time_ago": f"{timesince(chat.created_at)} ago"
        }
        for chat in chats
    ]
    return render(request, "chat.html", {"chats": chat_data})

logger = logging.getLogger(__name__)

# Directory to save uploaded/edited files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Attempt to import the OpenAI wrapper that x.ai says can be adapted.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

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
        # Log file details
        logger.info(f"Uploaded file: {uploaded_file.name} ({uploaded_file.content_type})")

        # Check file type and process accordingly
        if uploaded_file.name.endswith(".txt"):
            content = uploaded_file.read().decode("utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            try:
                reader = PdfReader(uploaded_file)
                content = " ".join(page.extract_text() for page in reader.pages if page.extract_text())
                if not content.strip():
                    return JsonResponse({"error": "No readable text found in the PDF."}, status=400)
            except Exception as e:
                logger.error(f"Error processing PDF file: {e}")
                return JsonResponse({"error": "Failed to process PDF file."}, status=500)
        else:
            return JsonResponse({"error": "Unsupported file type. Please upload a .txt or .pdf file."}, status=400)

        # Return extracted content
        return JsonResponse({"content": content})
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return JsonResponse({"error": "Error processing file."}, status=500)


@csrf_exempt
def save_file(request):
    """
    Saves the edited content of a file.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed."}, status=400)

    try:
        data = json.loads(request.body.decode("utf-8"))
        file_name = data.get("fileName")
        content = data.get("content")

        if not file_name or not content:
            return JsonResponse({"error": "File name and content are required."}, status=400)

        # Save the file content to the server
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "w", encoding="utf-8") as file:  # Ensure overwriting mode
            file.write(content)

        return JsonResponse({"success": True, "message": "File saved successfully!"})
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return JsonResponse({"error": f"Error saving file: {str(e)}"}, status=500)


@csrf_exempt
def save_script(request):
    """
    Save a chat script to the database.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=400)

    try:
        # Parse the incoming JSON payload
        data = json.loads(request.body.decode("utf-8"))
        message = data.get("message")
        response = data.get("response")

        if not message or not response:
            return JsonResponse({"error": "Message and response fields are required."}, status=400)

        # Save the script to the database
        Chat.objects.create(message=message, response=response)
        return JsonResponse({"message": "Script saved successfully!"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON payload."}, status=400)

    except Exception as e:
        logger.error(f"Error saving script: {e}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


@csrf_exempt
def get_scripts(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET requests are allowed."}, status=400)

    try:
        scripts = Chat.objects.all().order_by("-created_at")
        scripts_data = [
            {
                "id": script.id,  # Include the ID for future download links
                "message": script.message,
                "response": script.response,
                "created_at": script.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for script in scripts
        ]
        return JsonResponse({"scripts": scripts_data})
    except Exception as e:
        logger.error(f"Error retrieving scripts: {e}")
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=500)


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
                "content": "You are a helpful assistant that reads information provided and generates youtube video or instagram video scripts when prompted with the word script in the prompt."
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

        # Extract reply from API response
        if completion.choices and len(completion.choices) > 0:
            grok_reply = completion.choices[0].message.content
        else:
            grok_reply = "[No valid reply in response]"

        # Save the interaction to the database
        Chat.objects.create(message=user_message, response=grok_reply)

    except requests.exceptions.RequestException as req_err:
        logger.error(f"Request error: {req_err}")
        grok_reply = f"Network/HTTP error: {req_err}"
    except Exception as e:
        logger.error(f"Error processing response: {e}")
        grok_reply = f"Error reaching x.ai Grok: {e}"

    return JsonResponse({"reply": grok_reply})
