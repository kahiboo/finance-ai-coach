from django.shortcuts import render

# Public pages
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

# Auth pages
def login_view(request):
    return render(request, 'login.html')

def logout_view(request):
    return render(request, 'logout.html')

def signup(request):
    return render(request, 'signup.html')

# Core app pages
def dashboard(request):
    return render(request, 'dashboard.html')

def budget(request):
    return render(request, 'budget.html')

def reports(request):
    return render(request, 'reports.html')

def upload(request):
    return render(request, 'upload.html')

def contact(request):
    return render(request, 'contact.html')

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
