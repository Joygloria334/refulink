from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/identity/', include('apps.identity.urls')),
    path('api/wallet/', include('apps.wallet.urls')),
    # Pending: uncomment once apps.stellar.urls and apps.mpesa.urls are implemented
    # path('api/stellar/', include('apps.stellar.urls')),
    # path('api/mpesa/', include('apps.mpesa.urls')),
]
