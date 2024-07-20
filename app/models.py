from django.db import models
from datetime import datetime
from decimal import Decimal

class Accounts(models.Model):
    name = models.CharField(max_length=100)
    expense = models.FloatField(default=0)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    expense_list = models.ManyToManyField('Expense', blank=True)




class Expense(models.Model):
    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    long_term = models.BooleanField(default=False) 
    monthly_expenses = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)

    def __str__(self):
        return self.name


    

    def save(self, *args, **kwargs):
        if self.long_term:
            self.monthly_expenses = self.calculate_monthly_expenses()
        super(Expense, self).save(*args, **kwargs)
        
    def calculate_monthly_expenses(self):
        if self.long_term:
            amount = Decimal(self.amount)
            if self.interest_rate == 0:
                months = Decimal((self.end_date - self.date).days) / Decimal(30)  # Assuming a month has 30 days
                return amount / months
            else:
                months = (self.end_date.year - self.date.year) * 12 + (self.end_date.month - self.date.month)
                monthly_rate = Decimal(self.interest_rate) / Decimal(12) / Decimal(100)
                monthly_expense = (amount * monthly_rate) / (1 - (1 + monthly_rate) ** -months)
                return round(monthly_expense, 2)
        else:
            return self.monthly_expenses