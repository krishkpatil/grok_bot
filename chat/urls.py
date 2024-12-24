from django.contrib import admin
from django.urls import path
from chat.views import chat_page, send_message, upload_file, save_script, get_scripts

urlpatterns = [
    path("admin/", admin.site.urls),
    path("chat/", chat_page, name="chat_page"),  # Add this
    path("chat/send/", send_message, name="send_message"),
    path("chat/upload/", upload_file, name="upload_file"),
    path("chat/save/", save_script, name="save_script"),
    path("chat/scripts/", get_scripts, name="get_scripts"),
    path("chat/upload_file/", upload_file, name="upload_file"), 
]
