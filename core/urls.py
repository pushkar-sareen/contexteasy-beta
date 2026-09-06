from django.contrib import admin
from django.urls import path, include
from base.views import *
from chats.views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("health/", health),
    path('admin/', admin.site.urls),
    path('chat/', index, name='chat'),
    path('', homepage, name='homepage'),
    path('transaction/', transaction, name='transaction'),
    path('accounts/', include("allauth.urls")),
    path('', include("accounts.urls")),
    path('delete/', delete_chat, name="delete_chat"),
    path("delete-file/<int:id>/", delete_files, name="delete_file"),
    path("delete-link/<int:id>/", delete_link, name="delete_link"),
    path("delete-url/<int:id>/", delete_url, name="delete_url"),

]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )