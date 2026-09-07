from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Transaction, Category, Budget
from .forms import TransactionForm, CategoryForm
from django.http import HttpResponse
import csv
from django.db.models import Sum
from datetime import date
from decimal import Decimal


@login_required
def list_transactions(request):
    user = request.user
    qs = Transaction.objects.filter(user=user).order_by('-date')
    categories = Category.objects.filter(user__in=[None, user])

    today = date.today()
    month_start = date(today.year, today.month, 1)
    month_spending = qs.filter(date__gte=month_start).values('category__name').annotate(total=Sum('amount'))
    totals = {r['category__name'] or 'Uncategorized': float(r['total'] or 0) for r in month_spending}

    budgets = Budget.objects.filter(user=user, month__year=today.year, month__month=today.month)

    # Calculate spent per budget for overview table
    budget_data = []
    for b in budgets:
        spent = qs.filter(category=b.category, date__gte=month_start).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        limit = b.limit if isinstance(b.limit, Decimal) else Decimal(b.limit)
        remaining = limit - spent
        budget_data.append({
            'id': b.id,                      # 👈 add id so we can edit
            'category': b.category.name,
            'limit': float(limit),
            'spent': float(spent),
            'remaining': float(remaining),
        })

    # Generate insights (unchanged)
    insights = []
    for b in budgets:
        spent = qs.filter(category=b.category, date__gte=month_start).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        limit = b.limit if isinstance(b.limit, Decimal) else Decimal(b.limit)

        if spent > limit:
            insights.append(f"You exceeded budget for {b.category.name} (spent {spent}, limit {limit})")
        elif spent > limit * Decimal('0.9'):
            insights.append(f"You are close to your budget limit for {b.category.name}")

    from .forms import BudgetForm   # or put at top of file

    budget_form = BudgetForm()      # 👈 form to add new budget

    context = {
        'transactions': qs,
        'categories': categories,
        'totals': totals,
        'insights': insights,
        'budget_data': budget_data,
        'budget_form': budget_form,  # 👈 send to template
    }
    return render(request, 'transactions/list.html', context)


        # Generate insights
    insights = []

    # 1) Budget-based alerts (same idea as before)
    for b in budgets:
        spent = qs.filter(category=b.category, date__gte=month_start) \
                  .aggregate(total=Sum('amount'))['total'] or Decimal('0')
        limit = b.limit if isinstance(b.limit, Decimal) else Decimal(b.limit)

        if spent > limit:
            insights.append(
                f"You exceeded the budget for {b.category.name} "
                f"(spent ₹{float(spent):.2f}, limit ₹{float(limit):.2f})."
            )
        elif spent > limit * Decimal('0.9'):
            insights.append(
                f"You are close to your budget limit for {b.category.name} "
                f"(spent ₹{float(spent):.2f} of ₹{float(limit):.2f})."
            )

    # 2) General insights that always show when you have transactions this month
    if totals:  # totals dict is already computed earlier
        # total spending this month
        total_spent = sum(totals.values())
        insights.append(f"Your total spending this month is ₹{total_spent:.2f}.")

        # top spending category
        top_cat = max(totals, key=totals.get)
        insights.append(
            f"Your highest spending category this month is {top_cat} "
            f"(₹{totals[top_cat]:.2f})."
        )

        # small behaviour tips
        if len(totals) == 1:
            insights.append(
                "All your spending this month is in a single category. "
                "Try reducing that category or distributing expenses more evenly."
            )
        elif len(totals) >= 3:
            insights.append(
                "You are spending across many categories. "
                "Review non-essential categories like shopping or entertainment to save more."
            )


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.user = request.user
            t.save()
            return redirect('transactions:list')
    else:
        form = TransactionForm()
    return render(request, 'transactions/form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_transaction(request, pk):
    t = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=t)
        if form.is_valid():
            form.save()
            return redirect('transactions:list')
    else:
        form = TransactionForm(instance=t)
    return render(request, 'transactions/form.html', {'form': form, 'action': 'Edit'})


@login_required
def delete_transaction(request, pk):
    t = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        t.delete()
        return redirect('transactions:list')
    return render(request, 'transactions/form.html', {'confirm_delete': True, 'transaction': t})


@login_required
def export_csv(request):
    user = request.user
    qs = Transaction.objects.filter(user=user).order_by('-date')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    writer = csv.writer(response)
    writer.writerow(['Date', 'Amount', 'Category', 'Notes'])
    for t in qs:
        writer.writerow([t.date, t.amount, t.category.name if t.category else '', t.notes])
    return response

from .forms import TransactionForm, CategoryForm, BudgetForm  # update import
# ...

@login_required
def add_budget(request):
    today = date.today()
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category']
            limit = form.cleaned_data['limit']
            # create or update budget for this user + category + month
            Budget.objects.update_or_create(
                user=request.user,
                category=category,
                month=date(today.year, today.month, 1),
                defaults={'limit': limit},
            )
            return redirect('transactions:list')
    else:
        form = BudgetForm()
    return render(request, 'transactions/budget_form.html', {'form': form, 'action': 'Add'})


@login_required
def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            return redirect('transactions:list')
    else:
        form = BudgetForm(instance=budget)
    return render(request, 'transactions/budget_form.html', {'form': form, 'action': 'Edit'})
