from django.urls import path

from .views import (
    RegisterRefugeeIdentityView,
    RequestVouchView,
    TriggerOnChainVouchView,
    VerifyRINView,
    VouchStatusView,
)

app_name = "identity"

urlpatterns = [
    path("verify-rin/", VerifyRINView.as_view(), name="verify-rin"),
    path("register-identity/", RegisterRefugeeIdentityView.as_view(), name="register-identity"),
    path("request-vouch/", RequestVouchView.as_view(), name="request-vouch"),
    path("trigger-vouch/", TriggerOnChainVouchView.as_view(), name="trigger-vouch"),
    path("vouch-status/", VouchStatusView.as_view(), name="vouch-status"),
]
