from django.urls import path
from . import views

app_name = "transactions"

urlpatterns = [
    path("", views.transaction_list, name="list"),
    path("add/", views.transaction_add, name="add"),
    path("edit/<int:pk>/", views.transaction_edit, name="edit"),
    path("delete/<int:pk>/", views.transaction_delete, name="delete"),
    path("export-csv/", views.export_csv, name="export_csv"),
]
