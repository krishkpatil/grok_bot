from django.contrib import admin
from django.urls import path
from chat.views import chat_page, send_message

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', chat_page, name='chat_page'),        # home => chat.html
    path('chat/send', send_message, name='send_message'),
]
