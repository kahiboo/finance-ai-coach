import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


# ============================
# Custom User Manager
# ============================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, full_name=None):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, full_name=full_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, full_name=None):
        user = self.create_user(email, username, password, full_name)
        user.is_admin = True
        user.is_superuser = True   # Required for Django Admin
        user.is_staff = True       #  Makes admin login work
        user.save(using=self._db)
        return user


# ============================
# Custom User Model
# ============================
class CustomUser(AbstractBaseUser, PermissionsMixin):  # added PermissionsMixin
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=100, unique=True)
    full_name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email", "full_name"]

    objects = CustomUserManager()

    def __str__(self):
        return self.username

    @property
    def is_staff(self):
        return self.is_admin or self.is_superuser  # covers both admin/superuser

    # Optional: explicitly define these to silence admin complaints
    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser


# ============================
# Category Model
# ============================
class Category(models.Model):
    user = models.ForeignKey('mainpage.CustomUser', on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('user', 'name')


# ============================
# Transaction Model
# ============================
class Transaction(models.Model):
    user = models.ForeignKey('mainpage.CustomUser', on_delete=models.CASCADE, related_name='transactions')
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
    user = models.ForeignKey('mainpage.CustomUser', on_delete=models.CASCADE, related_name='goals')
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