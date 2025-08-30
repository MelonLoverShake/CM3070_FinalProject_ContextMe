from django.shortcuts import render, redirect
from .models import * 
from django.contrib import messages
from login.supabase_cilent import supabase
from django.utils import timezone
from datetime import datetime, timedelta
from .utils import get_user_statistics, update_user_login, update_admin_last_access,get_client_ip


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        sec_answer = request.POST.get('security_answer')

        try:
            admin_user = Admin_users.objects.get(username=username)

            # Check password
            if not admin_user.check_password(password):
                messages.error(request, "Incorrect password.")
                return render(request, 'Admin_Login.html', {'security_question': "What is your favourite music genre?"})

            # Check security question
            if not admin_user.check_SecurityQ(sec_answer):
                messages.error(request, "Incorrect security answer.")
                return render(request, 'Admin_Login.html', {'security_question': "What is your favourite music genre?"})

            # Login successful
            request.session['admin_id'] = str(admin_user.admin_id)
            request.session['admin_username'] = admin_user.username
            messages.success(request, f"Welcome back, {admin_user.username}!")
            return redirect('admin_app:Admin_Dashboard')

        except Admin_users.DoesNotExist:
            messages.error(request, "Admin not found.")

    
    return render(request, 'Admin_Login.html', {
        'security_question': "What is your favourite music genre?"
    })

def Admin_Dashboard(request):
    admin_id = request.session.get('admin_id')
    
    if not admin_id:
        return redirect('admin_login')  
    
    try:
        admin_user = Admin_users.objects.get(admin_id=admin_id)
        
        # Get user statistics from Supabase
        user_stats = get_user_statistics()
        
        # Update admin's last access
        update_admin_last_access(admin_id, request)
        
        context = {
            'admin_username': admin_user.username,
            'admin_user': admin_user,
            'total_users': user_stats['total_users'],
        }
        return render(request, 'Admin_Dashboard.html', context)
    except Admin_users.DoesNotExist:
        return redirect('admin_login')

