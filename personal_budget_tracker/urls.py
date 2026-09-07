from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('transactions/', include('transactions.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('', RedirectView.as_view(url='/transactions/')),
]
