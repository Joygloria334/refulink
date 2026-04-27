from django.conf import settings
from django.db import models


class TransactionLog(models.Model):
    """Internal audit record for every Stellar transaction initiated via RefuLink."""

    class Direction(models.TextChoices):
        SEND = "send", "Send"
        RECEIVE = "receive", "Receive"

    class TxStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transaction_logs",
    )
    tx_hash = models.CharField(max_length=64, unique=True, db_index=True)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    amount_kes = models.DecimalField(max_digits=14, decimal_places=2)
    counterparty_address = models.CharField(max_length=56)
    status = models.CharField(
        max_length=10,
        choices=TxStatus.choices,
        default=TxStatus.PENDING,
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "Transaction Log"
        verbose_name_plural = "Transaction Logs"

    def __str__(self):
        return (
            f"{self.user.username} {self.direction} "
            f"KES {self.amount_kes} — {self.tx_hash[:12]}"
        )
