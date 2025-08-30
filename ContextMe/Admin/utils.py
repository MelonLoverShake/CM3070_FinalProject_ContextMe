from datetime import datetime, timedelta
from login.supabase_cilent import supabase

def get_user_statistics():
    """Fetch user statistics from Supabase login_user table"""
    try:
        # Get current datetime
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)
        month_start = now - timedelta(days=30)
        
        # Format dates for Supabase (ISO format)
        today_iso = today_start.isoformat()
        week_iso = week_start.isoformat()
        month_iso = month_start.isoformat()
        
        # Total users count
        total_users_response = supabase.table('login_user').select('*', count='exact').execute()
        total_users = total_users_response.count if total_users_response.count else 0
        
        return {
            'total_users': total_users,
        }
        
    except Exception as e:
        print(f"Error fetching user statistics: {e}")
        return {
            'total_users': 0,
            'active_users_today': 0,
            'active_users_week': 0,
            'active_users_month': 0,
            'recent_logins': [],
            'new_registrations_today': 0,
            'new_registrations_week': 0,
        }

def update_admin_last_access(admin_id, request):
    """Update admin's last access time and IP"""
    try:
        ip = get_client_ip(request)
        now = datetime.now().isoformat()
        
    except Exception as e:
        print(f"Error updating admin access: {e}")

def update_user_login(email, request):
    """Function to update user login info - use this in your login view"""
    try:
        ip = get_client_ip(request)
        now = datetime.now().isoformat()
        
        update_response = supabase.table('login_user').update({
            'last_login_ip': ip,
            'last_login_time': now
        }).eq('email', email).execute()
        
        return update_response
        
    except Exception as e:
        print(f"Error updating user login: {e}")
        return None

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip