from django.urls import path

from .views import AuditLogView, BalanceView, SendTokenView, TransactionHistoryView

urlpatterns = [
    path("balance/", BalanceView.as_view(), name="wallet-balance"),
    path("transactions/", TransactionHistoryView.as_view(), name="wallet-transactions"),
    path("send/", SendTokenView.as_view(), name="wallet-send"),
    path("audit/", AuditLogView.as_view(), name="wallet-audit"),
]
