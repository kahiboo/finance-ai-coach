import uuid
from django.db import models
from django.contrib.auth import get_user_model



User = get_user_model()

# ============================
# Category Model
# ============================
class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')


# ============================
# Transaction Model
# ============================
class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    description = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description or 'Transaction'} - {self.amount}"


# ============================
# Savings Goal Model
# ============================
class SavingsGoal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    name = models.CharField(max_length=64, default='Main Goal')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)

    @property
    def progress_pct(self):
        if self.target_amount and self.target_amount != 0:
            return float(self.current_savings / self.target_amount * 100)
        return 0.0

    def __str__(self):
        return f"{self.name} ({self.progress_pct:.1f}%)"

#-------------------------------------
# Bank Connection
#-------------------------------------
class BankConnection(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="bank_connection")
    access_token = models.CharField(max_length=255, blank=True, null=True)
    item_id = models.CharField(max_length=255, blank=True, null=True)
    institution_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} Bank Connection"

