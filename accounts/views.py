from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm, LoginForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('accounts:login')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect('transactions:list')
        else:
            form.add_error(None, 'Invalid credentials')
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('accounts:login')

@login_required
def list_transactions(request):
    # Fetch all transactions for the logged-in user
    transactions = Transaction.objects.filter(user=request.user).order_by('-date')

    # Define budget per category (you can make this dynamic later)
    budgets = {}
    for category in Category.objects.all():
        budgets[category.name] = category.budget if hasattr(category, 'budget') else 500000

    # Calculate totals spent per category
    totals = {}
    for t in transactions:
        cat_name = t.category.name if t.category else 'Uncategorized'
        totals[cat_name] = totals.get(cat_name, 0) + float(t.amount)

    # Calculate remaining per category
    remaining = {}
    for cat_name, budget_amount in budgets.items():
        spent = totals.get(cat_name, 0)
        remaining[cat_name] = max(budget_amount - spent, 0)

    # Generate simple insights
    insights = []
    for cat_name, spent in totals.items():
        budget_amount = budgets.get(cat_name, 500)
        if spent > budget_amount:
            insights.append(f"Overspending alert: You spent ${spent:.2f} on {cat_name}, over your budget of ${budget_amount:.2f}.")
        elif spent > 0.8 * budget_amount:
            insights.append(f"Caution: You have used {spent:.2f}/${budget_amount:.2f} of your budget for {cat_name}.")
        else:
            insights.append(f"Good job! You spent ${spent:.2f} on {cat_name} within your budget of ${budget_amount:.2f}.")

    context = {
        'transactions': transactions,
        'totals': totals,
        'budgets': budgets,
        'remaining': remaining,
        'insights': insights,
    }

    return render(request, 'transactions/list.html', context)
@login_required(login_url='accounts:login')
def password_change(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user  # guaranteed to be logged in

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirmation do not match.")
        else:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)  # keep user logged in
            messages.success(request, "Password changed successfully!")
            return redirect('transactions:list')

    return render(request, 'accounts/password_change.html')