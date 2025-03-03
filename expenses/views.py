from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponse
from django.contrib.auth import login, logout, authenticate
from .models import Expense
from .forms import ExpenseForm, RegisterForm
from reportlab.pdfgen import canvas
from io import BytesIO
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import user_passes_test

def is_admin_or_manager(user):
    return user.is_superuser or user.groups.filter(name__in=["Admin", "Manager"]).exists()

def sign_up(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            group = Group.objects.get(name="User")
            user.groups.add(group)
            login(request, user)
            return redirect('/login')
    else:
        form = RegisterForm()
    return render(request, 'registration/sign_up.html', {"form": form})
    
def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard view with statistics
@login_required
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def dashboard(request):
    expenses = Expense.objects.filter(user=request.user, is_active=True)
    total_expense = sum(exp.amount for exp in expenses)
    category_expenses = {cat: sum(exp.amount for exp in expenses if exp.category == cat) for cat, _ in Expense.CATEGORY_CHOICES}
    return render(request, 'expenses/dashboard.html', {
        'expenses': expenses,
        'total_expense': total_expense,
        'category_expenses': category_expenses
    })

# List all expenses with filtering
@login_required
def expense_list(request):
    if request.user.groups.filter(name="Admin").exists():
        expenses = Expense.objects.filter(is_active=True)  # Admin sees all
    else:
        expenses = Expense.objects.filter(user=request.user, is_active=True)  # Users see only theirs
    # Filtering the expenses
    category_filter = request.GET.get('category')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if category_filter:
        expenses = expenses.filter(category=category_filter)
    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])
    return render(request, 'expenses/expense_list.html', {'expenses': expenses})

# Add new expense
@login_required
#@permission_required("expenses.add_expense", login_url="/login", raise_exception=True)
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def add_expense(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            # Assigning logged in user
            expense.user = request.user
            expense.save()
            return redirect('expense_list')
        else:
            print("Form is not valid:", form.errors)
    else:
        form = ExpenseForm()
    return render(request, 'expenses/expense_form.html', {'form': form})

# Update expense
@login_required
#@permission_required("expenses.update_expense", login_url="/login", raise_exception=True)
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def update_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user, is_active=True)
    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            expense.author = request.user
            form.save()
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'expenses/expense_form.html', {'form': form})

# Delete expense
@login_required
#@permission_required("expenses.delete_expense", login_url="/login", raise_exception=True)
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user, is_active=True)
    if request.method == 'POST':
        expense.author = request.user
        expense.delete()
        return redirect('expense_list')
    return render(request, 'expenses/expense_confirm_delete.html', {'expense': expense})

@login_required
#@permission_required("expenses.export_expenses_pdf", login_url="/login", raise_exception=True)
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def export_expenses_pdf(request):
    category_filter = request.GET.get('category', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    expenses = Expense.objects.filter(user=request.user, is_active=True)

    if category_filter:
        expenses = expenses.filter(category=category_filter)

    if start_date and end_date:
        expenses = expenses.filter(date__range=[start_date, end_date])

    if not expenses.exists():
        return HttpResponse("No expenses found for the selected filters.", content_type="text/plain")

    return generate_pdf(request, expenses)  
    
@login_required
#@permission_required("expenses.generate_pdf", login_url="/login", raise_exception=True) 
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def generate_pdf(request, expenses):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.setFont("Helvetica", 14)
    p.drawString(100, 800, "Filtered Expense Report")

    y = 780
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Date")
    p.drawString(150, y, "Title")
    p.drawString(300, y, "Amount")
    p.drawString(400, y, "Category")
    y -= 20
    p.setFont("Helvetica", 12)

    for expense in expenses:
        p.drawString(50, y, str(expense.date))
        p.drawString(150, y, expense.title[:20])  
        p.drawString(300, y, f"${expense.amount}")
        p.drawString(400, y, expense.category)
        y -= 20
        if y < 50:  
            p.showPage()
            p.setFont("Helvetica", 12)
            y = 780

    p.save()
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Filtered_Expense_Report.pdf"'
    return response

@login_required
@user_passes_test(is_admin_or_manager, login_url="/login", redirect_field_name=None)
def send_email_report(request):
    expenses = Expense.objects.filter(user=request.user, is_active=True)

    if not expenses.exists():  
        return HttpResponse("No expenses to report", content_type="text/plain")

    pdf_response = generate_pdf(request, expenses)
    pdf_data = pdf_response.content

    subject = "Check Your Expense Report"
    html_message = render_to_string('expenses/email_report.html', {'user': request.user, 'expenses': expenses})
    plain_message = strip_tags(html_message)
    
    email = EmailMessage(
        subject,
        plain_message,
        'jyotijakhar2401@gmail.com',  
        [request.user.email]
    )

    email.attach('Expense_Report.pdf', pdf_data, 'application/pdf')
    email.send()

    return HttpResponse("Expense report emailed successfully", content_type="text/plain")