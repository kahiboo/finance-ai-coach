from django.urls import path
from .views import (
    index, about, signup, login_view, logout_view, dashboard,
    upload_csv, reports, categories, contact, create_link_token, exchange_public_token, fetch_transactions, ai_suggestions, update_transaction_category, transactions, add_transaction, goal_view, delete_transaction)

urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('signup/', signup, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard, name='dashboard'),
    path('upload/', upload_csv, name='upload'),
    path('reports/', reports, name='reports'),
    path('categories/', categories, name='categories'),
    path('contact/', contact, name='contact'),
    path("ai/suggestions/", ai_suggestions, name="ai_suggestions"),
    path("update-category/<int:transaction_id>/", update_transaction_category, name="update_category"),
    path("transactions/", transactions, name="transactions"),
    path("transactions/add/", add_transaction, name="add_transaction"),
    path("goal/", goal_view, name="goal"),
    path("transactions/delete/<int:transaction_id>/", delete_transaction, name="delete_transaction"),




    # Plaid
    path("plaid/create_link_token/", create_link_token, name="create_link_token"),
    path("plaid/exchange_public_token/", exchange_public_token, name="exchange_public_token"),
    path("plaid/fetch_transactions/", fetch_transactions, name="fetch_transactions"),


]

