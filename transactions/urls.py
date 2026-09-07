from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.list_transactions, name='list'),
    path('add/', views.add_transaction, name='add'),
    path('edit/<int:pk>/', views.edit_transaction, name='edit'),
    path('delete/<int:pk>/', views.delete_transaction, name='delete'),
    path('export/csv/', views.export_csv, name='export_csv'),

    path('budget/add/', views.add_budget, name='add_budget'),              # 👈 new
    path('budget/<int:pk>/edit/', views.edit_budget, name='edit_budget'),  # 👈 new
]
