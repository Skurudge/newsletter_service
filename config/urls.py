from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("mailing.urls", namespace="mailing")),  # Ядро рассылок на главной странице
    path("users/", include("users.urls", namespace="users")),  # Аутентификация и пользователи
    path("blog/", include("blog.urls", namespace="blog")),  # Контентный блог
]

# Подключаем раздачу медиафайлов (картинок) в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
