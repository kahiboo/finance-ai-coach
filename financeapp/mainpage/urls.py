from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('reports/', views.reports, name='reports'),
    path('upload/', views.upload, name='upload'),
    path('contact/', views.contact, name='contact'),
    path('signup/', views.signup, name='signup'),
    path('categories/', views.categories, name='categories'),
    path('dashboard/', views.dashboard, name='dashboard'),

]

