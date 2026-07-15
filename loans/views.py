from django.shortcuts import render
from django.http import HttpResponse
from .forms import CustomerDetailsForm, BankDetailsFormSet
from .pdf_generator import generate_pie_chart, generate_brochure_pdf, get_base64_image
from decimal import Decimal
import os
from django.conf import settings

def calculate_emi(principal, roi_annual, tenure_months):
    if roi_annual == 0:
        return principal / tenure_months
    r = (roi_annual / 12) / 100
    n = tenure_months
    emi = principal * r * ((1 + r)**n) / (((1 + r)**n) - 1)
    return emi

def index_view(request):
    return render(request, 'loans/landing.html')

def calculator_view(request):
    return render(request, 'loans/calculator.html')

def calculator_report_view(request):
    if request.method == 'POST':
        from .pdf_generator import generate_quotation_pdf
        client_name = request.POST.get('client_name', 'Valued Client')
        try:
            principal = float(request.POST.get('loan_amount', 0))
            roi = float(request.POST.get('roi', 0))
            tenure = int(request.POST.get('tenure', 0))
        except ValueError:
            return HttpResponse("Invalid input data", status=400)

        emi = calculate_emi(principal, roi, tenure)
        total_payable = emi * tenure
        total_interest = total_payable - principal

        # Amortization Schedule
        schedule = []
        balance = principal
        monthly_rate = (roi / 12) / 100

        for month in range(1, tenure + 1):
            if roi == 0:
                interest_payment = 0
                principal_payment = emi
            else:
                interest_payment = balance * monthly_rate
                principal_payment = emi - interest_payment
            
            balance -= principal_payment
            if balance < 0:
                balance = 0
            
            schedule.append({
                'month': month,
                'emi': round(emi, 2),
                'interest': round(interest_payment, 2),
                'principal': round(principal_payment, 2),
                'balance': round(balance, 2)
            })

        chart_base64 = generate_pie_chart(principal, total_interest)
        
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'loans', 'efb_without_bg.png')
        logo_base64 = get_base64_image(logo_path)

        context_data = {
            'client_name': client_name,
            'principal': round(principal, 2),
            'roi': roi,
            'tenure': tenure,
            'emi': round(emi, 2),
            'total_interest': round(total_interest, 2),
            'total_payable': round(total_payable, 2),
            'schedule': schedule,
            'chart_base64': chart_base64,
            'logo_url': logo_base64
        }

        pdf_bytes = generate_quotation_pdf(context_data)
        
        if pdf_bytes:
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="Quotation_{client_name.replace(" ", "_")}.pdf"'
            return response
        else:
            return HttpResponse("Error generating PDF", status=500)
    
    return HttpResponse("Method not allowed", status=405)

def comparison_view(request):
    if request.method == 'POST':
        customer_form = CustomerDetailsForm(request.POST)
        bank_formset = BankDetailsFormSet(request.POST)
        
        if customer_form.is_valid() and bank_formset.is_valid():
            customer_data = customer_form.cleaned_data
            # --- Calculation Logic (Summing comma-separated values) ---
            def sum_comma_values(value):
                if not value:
                    return 0
                if isinstance(value, (int, float, Decimal)):
                    return float(value)
                # Split by comma, remove whitespace, and sum
                try:
                    return sum(float(x.strip()) for x in str(value).split(',') if x.strip())
                except ValueError:
                    return 0

            loan_liab_sum = sum_comma_values(customer_data.get('loan_liabilities'))
            cc_limit_sum = sum_comma_values(customer_data.get('credit_card_limit'))
            
            # 5% of Credit Card Limit is a liability
            cc_liabilities = cc_limit_sum * 0.05
            total_liabilities = loan_liab_sum + cc_liabilities
            
            # Add calculated values to the dictionary passed to the PDF generator
            customer_data['calculated_total_liabilities'] = total_liabilities
            # --------------------------
            
            # Use 0 if desired_amount is not provided (as it was removed from UI)
            principal = customer_data.get('desired_amount') or 0
            customer_data['desired_amount'] = principal
            
            # Process Bank Forms
            bank_comparisons = []
            
            deferment_applied = customer_data.get('deferment_applied', 'No')
            deferment_type = customer_data.get('deferment_type', 'Days')
            deferment_days = customer_data.get('deferment_days')
            deferment_months = customer_data.get('deferment_months')

            if deferment_applied == 'Yes':
                if deferment_type == 'Days' and deferment_days:
                    customer_data['deferment_duration_text'] = f"{deferment_days} Days"
                elif deferment_type == 'Months' and deferment_months:
                    customer_data['deferment_duration_text'] = f"{deferment_months} Months"
                else:
                    deferment_applied = 'No'
                    customer_data['deferment_applied'] = 'No'

            for form in bank_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    bank_name = form.cleaned_data.get('bank_name')
                    loan_amount = form.cleaned_data.get('loan_amount', principal)
                    roi = form.cleaned_data.get('roi')
                    tenure = form.cleaned_data.get('tenure')
                    
                    emi = calculate_emi(float(loan_amount), float(roi), tenure)
                    
                    # --- Deferment Logic ---
                    if deferment_applied == 'Yes':
                        deferment_interest = 0
                        if deferment_type == 'Days' and deferment_days:
                            deferment_interest = float(loan_amount) * (float(roi) / 100) * (deferment_days / 365)
                        elif deferment_type == 'Months' and deferment_months:
                            deferment_interest = float(loan_amount) * (float(roi) / 100) * (deferment_months / 12)
                        
                        additional_monthly_amount = deferment_interest / tenure
                        emi = emi + additional_monthly_amount
                        
                    total_payable = emi * tenure
                    total_interest = total_payable - float(loan_amount)
                    # -----------------------
                    
                    chart_base64 = generate_pie_chart(loan_amount, total_interest)
                    
                    bank_comparisons.append({
                        'bank_name': bank_name,
                        'loan_amount': round(float(loan_amount), 2),
                        'roi': roi,
                        'tenure': tenure,
                        'monthly_emi': round(emi, 2),
                        'total_interest': round(total_interest, 2),
                        'total_payable': round(total_payable, 2),
                        'chart_base64': chart_base64
                    })
            
            # Generate PDF
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'loans', 'efb_without_bg.png')
            logo_base64 = get_base64_image(logo_path)
            pdf_bytes = generate_brochure_pdf(customer_data, bank_comparisons, logo_base64)
            
            if pdf_bytes:
                response = HttpResponse(pdf_bytes, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="EFB_Loan_Comparison_{customer_data.get("customer_name")}.pdf"'
                return response
            else:
                return HttpResponse("Error generating PDF", status=500)
    else:
        customer_form = CustomerDetailsForm()
        bank_formset = BankDetailsFormSet()
        
    return render(request, 'loans/comparison.html', {
        'customer_form': customer_form,
        'bank_formset': bank_formset,
    })
