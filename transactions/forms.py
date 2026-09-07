from django import forms
from .models import Transaction, Category
from django import forms
from .models import Transaction, Category, Budget   # you already have some of these


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'limit']   # user + month will be set in the view


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'category', 'date', 'notes']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
