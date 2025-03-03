from django.urls import path
from expenses import views
from .views import expense_list, add_expense, update_expense, delete_expense

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('dashboard', views.dashboard, name='dashboard'),
    path("sign-up", views.sign_up, name="sign_up"),
    path("login/sign-up", views.sign_up, name="sign_up"),
    path('logout/', views.logout_view, name='logout'),
    path('expenses', views.expense_list, name='expense_list'),
    path('expenses/add/', views.add_expense, name='add_expense'),
    path('expenses/update/<int:expense_id>', views.update_expense, name='update_expense'),
    path('expenses/delete/<int:expense_id>', views.delete_expense, name='delete_expense'),
    path('expenses/export_pdf/', views.export_expenses_pdf, name='export_expenses_pdf'),
    path('expenses/generate_pdf/', views.generate_pdf, name='generate_pdf'),
    path('expenses/send_report/', views.send_email_report, name='send_email_report'),

]
