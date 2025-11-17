from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.utils import timezone
from .models import Transaction, Category, SavingsGoal
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password
import uuid
import pandas as pd
from io import TextIOWrapper

# Create your views here.

def index(request):
    return render(request,'index.html')

def dashboard(request):
    return render(request, 'dashboard.html')

def about(request):
    return render(request, 'about.html')

def reports(request):
    return render(request, 'reports.html')

def upload(request):
    return render(request, 'upload.html')

def contact(request):
    return render(request, 'contact.html')

def signup(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Validation
        if not all([full_name, email, username, password]):
            messages.error(request, "All fields are required.")
            return redirect("signup")

        with connection.cursor() as cursor:
            # Check for existing username or email
            cursor.execute("SELECT COUNT(*) FROM users WHERE email = %s OR username = %s", [email, username])
            if cursor.fetchone()[0] > 0:
                messages.error(request, "Email or username already exists.")
                return redirect("signup")

            # Hash the password before storing
            hashed_pw = make_password(password)

            # Insert the new user
            cursor.execute(
                """
                INSERT INTO users (id, email, full_name, username, password, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                [str(uuid.uuid4()), email, full_name, username, hashed_pw]
            )

        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")

    return render(request, "signup.html")

@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    start_month = today.replace(day=1)

    qs = Transaction.objects.filter(user=user, date__gte=start_month, date__lte=today)
    income = qs.filter(amount__gt=0).aggregate(total=Sum('amount'))['total'] or 0
    spend  = qs.filter(amount__lt=0).aggregate(total=Sum('amount'))['total'] or 0
    safe_to_spend = income + spend  # spend is negative

    goal = SavingsGoal.objects.filter(user=user).first()
    return render(request, 'index.html', {
        'income': income, 'spend': abs(spend),
        'safe_to_spend': safe_to_spend,
        'goal': goal,
    })

@login_required
def upload_csv(request):
    message = None
    if request.method == 'POST' and request.FILES.get('csv_file'):
        # Expect columns: date, description, amount, category (category optional)
        f = TextIOWrapper(request.FILES['csv_file'].file, encoding='utf-8')
        df = pd.read_csv(f)
        df.columns = [c.strip().lower() for c in df.columns]

        for _, row in df.iterrows():
            cat_obj = None
            if 'category' in df.columns and pd.notna(row.get('category')):
                cat_name = str(row['category']).strip()[:64]
                cat_obj, _ = Category.objects.get_or_create(user=request.user, name=cat_name)

            Transaction.objects.create(
                user=request.user,
                date=pd.to_datetime(row['date']).date(),
                description=str(row.get('description', '')).strip()[:255],
                amount=row['amount'],
                category=cat_obj
            )
        message = "CSV imported successfully."
    return render(request, 'upload.html', {'message': message})

@login_required
def reports(request):
    user = request.user
    # Monthly totals for last 6 months
    qs = (Transaction.objects
          .filter(user=user)
          .values('date__year','date__month')
          .annotate(total=Sum('amount'))
          .order_by('date__year','date__month'))
    # Prepare simple arrays for Chart.js
    labels = [f"{x['date__year']}-{x['date__month']:02d}" for x in qs]
    data = [float(x['total']) for x in qs]
    return render(request, 'reports.html', {'labels': labels, 'data': data})

@login_required
def categories(request):
    user = request.user
    if request.method == 'POST':
        name = request.POST.get('name','').strip()
        if name:
            Category.objects.get_or_create(user=user, name=name[:64])
        return redirect('categories')
    return render(request, 'categories.html', {'categories': user.categories.all()})

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if not username or not password:
            messages.error(request, "All fields are required.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        User.objects.create_user(username=username, password=password)
        messages.success(request, "Account created successfully!")
        return redirect("login")

    return render(request, "register.html")
