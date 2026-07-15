from django import forms
from django.forms import formset_factory

class CustomerDetailsForm(forms.Form):
    TOP_UP_CHOICES = [
        ('No', 'No'),
        ('Yes', 'Yes'),
    ]
    
    DEFERMENT_CHOICES = [
        ('No', 'No'),
        ('Yes', 'Yes'),
    ]

    DEFERMENT_TYPE_CHOICES = [
        ('Days', 'Days'),
        ('Months', 'Months'),
    ]
    
    customer_name = forms.CharField(max_length=100, required=True, label="Customer Name")
    # --- New Fields ---
    deferment_applied = forms.ChoiceField(choices=DEFERMENT_CHOICES, required=False, label="Deferment Applied?", initial='No')
    deferment_type = forms.ChoiceField(choices=DEFERMENT_TYPE_CHOICES, required=False, label="Deferment Type", initial='Days')
    deferment_days = forms.IntegerField(required=False, label="Deferment Days", min_value=1)
    deferment_months = forms.IntegerField(required=False, label="Deferment Months", min_value=1)
    monthly_salary = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label="Monthly Salary (AED)")
    loan_liabilities = forms.CharField(required=False, label="Existing Loan EMI Liabilities (AED)")
    credit_card_limit = forms.CharField(required=False, label="Total Credit Card Limit (AED)")
    # ------------------
    desired_amount = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label="Desired Amount (AED)")
    need_top_up = forms.ChoiceField(choices=TOP_UP_CHOICES, required=False, label="Need Top-up?")
    top_up_amount = forms.DecimalField(max_digits=12, decimal_places=2, required=False, label="Top-up Amount (AED)")

class BankDetailsForm(forms.Form):
    bank_name = forms.CharField(max_length=100, required=True, label="Bank Name")
    loan_amount = forms.DecimalField(max_digits=12, decimal_places=2, required=True, label="Loan Amount")
    roi = forms.DecimalField(max_digits=5, decimal_places=2, required=True, label="ROI (%)")
    tenure = forms.IntegerField(required=True, label="Tenure (Months)", min_value=1)

BankDetailsFormSet = formset_factory(BankDetailsForm, extra=1, can_delete=True)
