from django.http import HttpResponse
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('polls/', include('polls.urls')),
    path('admin/', admin.site.urls),
    path("ssrf-test/", lambda request: HttpResponse("Verified"), name="ssrf-test"),
]