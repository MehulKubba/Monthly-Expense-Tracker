# forms.py
from django import forms
from .models import Expense

class ExpenseForm(forms.ModelForm):
    long_term = forms.BooleanField(required=False)

    class Meta:
        model = Expense
        fields = ('name', 'amount', 'date', 'end_date', 'interest_rate', 'long_term')

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'long_term': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        long_term = cleaned_data.get("long_term")

        if long_term:
            if not cleaned_data.get("end_date"):
                self.add_error('end_date', "End date is required for long term expenses.")
            if not cleaned_data.get("interest_rate"):
                self.add_error('interest_rate', "Interest rate is required for long term expenses.")
        else:
            cleaned_data['end_date'] = None
            cleaned_data['interest_rate'] = None

        return cleaned_data
