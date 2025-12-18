# core/urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/farmer/', views.farmer_dashboard, name='farmer_dashboard'),
    path('dashboard/doctor/', views.doctor_dashboard, name='doctor_dashboard'),
    path('dashboard/doctor/chat-history/', views.doctor_chat_history, name='doctor_chat_history'),
    path('dashboard/farmer/cattle/', views.manage_cattle, name='manage_cattle'),
    path('dashboard/farmer/performance/', views.performance, name='performance'),
    path('dashboard/farmer/inventory/', views.inventory, name='inventory'),
    path('dashboard/inventory/update/<int:pk>/', views.update_inventory, name='update_inventory'),
    path('connect/doctors/', views.doctor_list, name='doctor_list'),
    path('connect/inbox/', views.inbox, name='inbox'),
    path('connect/chat/<int:user_id>/', views.chat_view, name='chat_view'),
]