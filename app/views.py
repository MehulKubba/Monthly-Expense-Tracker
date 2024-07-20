from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import FormView
from collections import defaultdict
from django.utils.safestring import mark_safe
from dateutil.relativedelta import relativedelta
import plotly.express as px
from datetime import timedelta
import plotly.graph_objs as go

from .models import Accounts, Expense
from .forms import ExpenseForm
from django.http import JsonResponse
import json
import logging






def home(request):
    return render(request, 'home/home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registration.html', {'form': form})

logger = logging.getLogger(__name__)

def generate_graph(data):
    fig = px.bar(data, x='months', y='expenses', title='Monthly Expenses')
    fig.update_layout(
        xaxis=dict(rangeslider=dict(visible=True)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color='rgba(0,0,0,1)',
    )
    fig.update_traces(marker_color='#008c41')
    graph_json = fig.to_json()
    return graph_json

class ExpenseListView(FormView):
    template_name = 'expenses/expense_list.html'
    form_class = ExpenseForm
    success_url = '/'  # Update this with the correct URL

    def form_valid(self, form):
        account, _ = Accounts.objects.get_or_create(user=self.request.user)
        
        expense = Expense(
            name=form.cleaned_data['name'],
            amount=form.cleaned_data['amount'],
            interest_rate=form.cleaned_data['interest_rate'],
            date=form.cleaned_data['date'],
            end_date=form.cleaned_data['end_date'],
            long_term=form.cleaned_data['long_term'],
            user=self.request.user
        )
        expense.save()
        account.expense_list.add(expense)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Initialize dictionaries to store data
        expense_data_graph = {}
        expense_data = {}
        long_term_expenses_summary = {}

        # Retrieve accounts belonging to the current user
        accounts = Accounts.objects.filter(user=user)

        # Process each account's expenses
        for account in accounts:
            expenses = account.expense_list.all()
            for expense in expenses:
                if expense.long_term and expense.monthly_expenses is not None and expense.date is not None:
                    year_month = expense.date.strftime('%Y-%m')
                    if year_month not in expense_data_graph:
                        expense_data_graph[year_month] = []

                    if expense.name not in long_term_expenses_summary:
                        long_term_expenses_summary[expense.name] = {
                            'monthly_amount': expense.monthly_expenses,
                            'date_from': expense.date,
                            'date_to': expense.end_date or expense.date
                        }

                    current_date = expense.date
                    end_date = expense.end_date or current_date  # Handle NoneType end_date
                    if end_date is not None:
                        while current_date <= end_date:
                            current_date += relativedelta(months=1)
                elif not expense.long_term and expense.date is not None:
                    year_month = expense.date.strftime('%Y-%m')
                    if year_month not in expense_data_graph:
                        expense_data_graph[year_month] = []

                    expense_data_graph[year_month].append({
                        'name': expense.name,
                        'amount': expense.amount,
                        'date': expense.date,
                    })

        # Prepare expense_data dictionary for displaying expenses
        for account in accounts:
            expenses = account.expense_list.all()
            for expense in expenses:
                if not expense.long_term and expense.date is not None:
                    year_month = expense.date.strftime('%Y-%m')
                    if year_month not in expense_data:
                        expense_data[year_month] = []

                    expense_data[year_month].append({
                        'name': expense.name,
                        'amount': expense.amount,
                        'date': expense.date,
                    })

        # Add long-term expenses summary to the expense_data dictionary
        for name, details in long_term_expenses_summary.items():
            year_month = "Long Term"
            if year_month not in expense_data:
                expense_data[year_month] = []

            expense_data[year_month].append({
                'name': name,
                'amount': details['monthly_amount'],
                'date_from': details['date_from'],
                'date_to': details['date_to'],
                'long_term': True,
            })

        # Convert the expense_data_graph into aggregated_data
        aggregated_data = [{'year_month': key, 'expenses': sum(item['amount'] for item in value)} for key, value in expense_data_graph.items()]

        # Prepare data for generating the Plotly graph
        graph_data = {
            'months': [item['year_month'] for item in aggregated_data],
            'expenses': [item['expenses'] for item in aggregated_data]
        }
        graph_data['chart'] = generate_graph(graph_data)
        context['graph_data'] = mark_safe(graph_data['chart'])  # Use mark_safe to render the JSON as HTML

        # Add data to the context
        context['expense_data'] = expense_data
        context['aggregated_data'] = aggregated_data

        return context