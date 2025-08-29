from django.shortcuts import render, redirect
from .models import * 
from django.contrib import messages

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

    # GET request or failed login
    return render(request, 'Admin_Login.html', {
        'security_question': "What is your favourite music genre?"
    })


def Admin_Dashboard(request):
    return render(request, 'Admin_Dashboard.html')