from django.contrib import admin
from django.urls import path
from chat.views import chat_page, send_message, upload_file, get_scripts, save_file

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", chat_page, name="chat_page"),  # Add this to serve the chat page at the root URL
    path("chat/", chat_page, name="chat_page"),
    path("chat/send/", send_message, name="send_message"),
    path("chat/upload_file/", upload_file, name="upload_file"),
    path("chat/save_file/", save_file, name="save_file"),
    path("chat/scripts/", get_scripts, name="get_scripts"),
]
