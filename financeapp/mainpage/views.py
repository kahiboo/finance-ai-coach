from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
User = get_user_model()
from django.db.models import Sum, Q
from django.utils import timezone
from django.contrib import messages
from plaid.model.country_code import CountryCode
from .models import Transaction, Category, SavingsGoal, BankConnection
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from datetime import datetime, timedelta
import pandas as pd
from io import TextIOWrapper
from .plaid_client import plaid_client
from django.http import JsonResponse
from plaid.model.products import Products
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from .ai_advice import generate_spending_advice
import logging
logger = logging.getLogger(__name__)


# -----------------------------
# PUBLIC PAGES
# -----------------------------

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def upload(request):
    return render(request, 'upload.html')

def contact(request):
    return render(request, 'contact.html')


# -----------------------------
# AUTHENTICATION
# -----------------------------

def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already in use.")
            return redirect("signup")

        # Create user
        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=password,
        )

        # OPTIONAL: If you want to store full name
        user.save()

        messages.success(request, "Account created! You can now log in.")
        return redirect("login")

    return render(request, "signup.html")


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect("dashboard")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, "login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('index')


# -----------------------------
# DASHBOARD (MAIN APP)
# -----------------------------

@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    start_month = today.replace(day=1)
    recent = Transaction.objects.filter(user=request.user).order_by('-date')[:10]

    qs = Transaction.objects.filter(user=user, date__gte=start_month, date__lte=today)
    income = qs.filter(amount__gt=0).aggregate(total=Sum('amount'))['total'] or 0
    spend = qs.filter(amount__lt=0).aggregate(total=Sum('amount'))['total'] or 0
    safe_to_spend = income + spend  # spend is negative

    goal = SavingsGoal.objects.filter(user=user).first()

    user_categories = Category.objects.filter(user=user)


    return render(request, 'dashboard.html', {
        'income': income,
        'spend': abs(spend),
        'safe_to_spend': safe_to_spend,
        'goal': goal,
        'recent': recent,
        'categories': user_categories,
    })

#================================
# Reports Page 
#===============================
@login_required
def reports(request):
    user = request.user

    # Monthly totals
    qs = (
        Transaction.objects
        .filter(user=user)
        .values("date__year", "date__month")
        .annotate(total=Sum("amount"))
        .order_by("date__year", "date__month")
    )

    month_labels = [f"{x['date__year']}-{x['date__month']:02d}" for x in qs]
    month_data = [float(x["total"]) for x in qs]

    total_net_activity = sum(month_data) if month_data else 0

    # Category totals
    cat_qs = (
        Transaction.objects
        .filter(user=user, category__isnull=False)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("category__name")
    )

    cat_labels = [c["category__name"] for c in cat_qs]
    cat_data = [float(c["total"]) for c in cat_qs]

    # Soft sky/corporate color palette
    cat_colors = [
        "#3B82F6", "#60A5FA", "#93C5FD", "#BFDBFE", "#1E3A8A",
        "#1D4ED8", "#2563EB", "#38BDF8", "#0EA5E9", "#0284C7"
    ]

    # Combine into one structure so templates stay clean
    category_chart = [
        {
            "label": cat_labels[i],
            "value": cat_data[i],
            "color": cat_colors[i % len(cat_colors)]
        }
        for i in range(len(cat_labels))
    ]

    return render(request, "reports.html", {
        "month_labels": month_labels,
        "month_data": month_data,
        "total_net_activity": total_net_activity,
        "category_chart": category_chart,
    })

# -----------------------------
# CSV UPLOAD
# -----------------------------

@login_required
def upload_csv(request):
    message = None

    if request.method == 'POST' and request.FILES.get('csv_file'):
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

#============================
#======= Transactions  ======
#============================


@login_required
def transactions(request):
    user = request.user

    # ---- Filters ----
    search_query = request.GET.get("q", "")
    month = request.GET.get("month", "")

    transactions = Transaction.objects.filter(user=user).order_by("-date")

    # Search (description or category name)
    if search_query:
        transactions = transactions.filter(
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    # Filter by month (format: 2025-05)
    if month:
        year, month_num = month.split("-")
        transactions = transactions.filter(date__year=year, date__month=month_num)

    # Month dropdown values
    months = (
        Transaction.objects.filter(user=user)
        .dates("date", "month", order="DESC")
    )

    return render(request, "transactions.html", {
        "transactions": transactions,
        "months": months,
        "search_query": search_query,
        "selected_month": month,
        "categories": Category.objects.filter(user=user),
    })



# -----------------------------
# CATEGORIES
# -----------------------------

@login_required
def categories(request):
    user = request.user
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if name:
            Category.objects.get_or_create(user=user, name=name[:64])
        return redirect('categories')

    return render(request, 'categories.html', {'categories': user.categories.all()})


#=============================
# ======= AI Suggest ========
#=============================
@login_required
def ai_suggestions(request):
    try:
        # Build simplified transaction list
        tx = Transaction.objects.filter(user=request.user).order_by("-date")[:50]

        combined = []
        for t in tx:
            combined.append(f"{t.date} | {t.description} | {t.amount}")

        tx_text = "\n".join(combined)

        ai_output = generate_spending_advice(tx_text)

        return JsonResponse({"advice": ai_output})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

#===============================
#======= Update Category =======
#===============================
@login_required
def update_transaction_category(request, transaction_id):
    if request.method == "POST":
        new_category_id = request.POST.get("category_id")
        transaction = get_object_or_404(Transaction, id=transaction_id)
        new_category = get_object_or_404(Category, id=new_category_id)

        transaction.category = new_category
        transaction.save()

        return JsonResponse({"success": True, "category_name": new_category.name})

    return JsonResponse({"success": False}, status=400)


#-------------------------------
# PLAID INTERGRATION
#-------------------------------
@login_required
def create_link_token(request):
    try:
        link_request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Finance AI Coach",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(
                client_user_id=str(request.user.id)
            ),
        )

        response = plaid_client.link_token_create(link_request)
        return JsonResponse(response.to_dict())

    except Exception as e:
        print("PLAID LINK TOKEN ERROR:", e)
        return JsonResponse({"error": str(e)}, status=400)

#==============================
#Exhange Public Token
#==============================
@login_required
def exchange_public_token(request):
    public_token = request.POST.get("public_token")

    if not public_token:
        return JsonResponse({"error": "public_token missing"}, status=400)

    try:
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=public_token
        )
        exchange_response = plaid_client.item_public_token_exchange(exchange_request)

        access_token = exchange_response.access_token
        item_id = exchange_response.item_id

        # Save to BankConnection
        connection, created = BankConnection.objects.get_or_create(user=request.user)
        connection.access_token = access_token
        connection.item_id = item_id
        connection.save()

        return JsonResponse({"status": "connected"})

    except Exception as e:
        print("PLAID EXCHANGE ERROR:", e)
        return JsonResponse({"error": str(e)}, status=400)

#===========================================
# Fetch Transactions
#===========================================
@login_required
def fetch_transactions(request):
    try:
        connection = BankConnection.objects.get(user=request.user)
        access_token = connection.access_token

        if not access_token:
            return JsonResponse({"error": "No bank connection found."}, status=400)

        # real date objects
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # build plaid request
        request_data = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,  
            end_date=end_date,  
            options=TransactionsGetRequestOptions(
                include_personal_finance_category=True
            )
        )

        plaid_response = plaid_client.transactions_get(request_data)
        transactions = plaid_response.to_dict().get("transactions", [])

        for tx in transactions:
            amount = tx["amount"]
            date = tx["date"]
            name = tx["name"]

            # Category
            category_obj = None
            if tx.get("personal_finance_category"):
                cat_name = tx["personal_finance_category"]["primary"][:64]
                category_obj, _ = Category.objects.get_or_create(
                    user=request.user,
                    name=cat_name
                )

            # Prevent duplicates
            if not Transaction.objects.filter(
                user=request.user,
                date=date,
                description=name,
                amount=amount
            ).exists():
                Transaction.objects.create(
                    user=request.user,
                    date=date,
                    description=name,
                    amount=-abs(amount),
                    category=category_obj
                )

        return JsonResponse({
            "status": "imported",
            "count": len(transactions)
        })

    except Exception as e:
        logger.error("PLAID FETCH ERROR: %s", str(e), exc_info=True)
        return JsonResponse({"error": str(e)}, status=400)
