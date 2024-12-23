from django.contrib import admin
from django.urls import path
from chat.views import chat_page, send_message, upload_file

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", chat_page, name="chat_page"),
    path("chat/send", send_message, name="send_message"),
    path("chat/upload", upload_file, name="upload_file"),
]
