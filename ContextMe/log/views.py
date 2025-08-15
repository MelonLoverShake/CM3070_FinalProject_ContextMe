from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
import json
from login.models import User
from log.models import ActivityLog

def activity_log_list(request):
    # Step 1: Get Supabase session data
    supabase_user_raw = request.session.get('supabase_user')
    if not supabase_user_raw:
        return redirect('login')

    # Step 2: Parse session JSON if needed
    if isinstance(supabase_user_raw, str):
        try:
            supabase_user_data = json.loads(supabase_user_raw)
        except json.JSONDecodeError:
            return redirect('login')
    elif isinstance(supabase_user_raw, dict):
        supabase_user_data = supabase_user_raw
    else:
        return redirect('login')

    # Step 3: Extract email
    email = supabase_user_data.get('email')
    if not email:
        return redirect('login')

    # Step 4: Get matching user
    user = get_object_or_404(User, email=email)

    # Step 5: Fetch logs for that user
    logs_qs = ActivityLog.objects.filter(user=user).order_by('-created_at')

    # Step 6: Paginate results
    paginator = Paginator(logs_qs, 10)  # 10 logs per page
    page_number = request.GET.get('page')
    logs = paginator.get_page(page_number)

    # Step 7: Render template
    return render(request, 'activity_log_list.html', {'logs': logs})
