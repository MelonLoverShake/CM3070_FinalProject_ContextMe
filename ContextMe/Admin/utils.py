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

        total_personas = get_users_personas()
        
        average_personas = get_average_personas()

        recent_logins = get_recent_logins()

        # Total users count
        total_users_response = (
            supabase.table("login_user").select("*", count="exact").execute()
        )
        total_users = total_users_response.count if total_users_response.count else 0

        return {
            "total_users": total_users,
            "total_personas" : total_personas,
            "average_personas": average_personas,
            "recent_logins": recent_logins,  # Add this
        }

    except Exception as e:
        print(f"Error fetching user statistics: {e}")
        return {
            "total_users": 0,
            "total_personas":0,
            "average_personas":0,
            "recent_logins": [],
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

        update_response = (
            supabase.table("login_user")
            .update({"last_login_ip": ip, "last_login_time": now})
            .eq("email", email)
            .execute()
        )

        return update_response

    except Exception as e:
        print(f"Error updating user login: {e}")
        return None


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def get_users_personas():
    """Get users personas count from supabase"""
    try:
        users_persona_response = (
            supabase.table("main_persona").select("*", count="exact").execute()
        )
        return users_persona_response.count if users_persona_response.count else 0

    except Exception as e:
        print(f"Error fetching personas count: {e}")
        return 0

def get_average_personas():
    """Get users average personas count from supabase"""
    try:
        total_users_response = (
            supabase.table("login_user").select("*", count="exact").execute()
        )
        total_users = total_users_response.count if total_users_response.count else 0

        users_persona_response = (
            supabase.table("main_persona").select("*", count="exact").execute()
        )
        return users_persona_response.count if users_persona_response.count else 0

        # Calculate average (avoid division by zero)
        if total_users > 0:
            average = total_personas / total_users
            return round(average, 1)  # Round to 1 decimal place
        else:
            return 0

    except Exception as e:
        print(f"Error calculating average personas: {e}")
        return 0
def get_recent_logins(limit=10):
    """Get recent login users with their persona counts"""
    try:
        # Get recent users (ordered by created_at instead)
        users_response = (
            supabase.table("login_user")
            .select("email, created_at, id")  
            .order("created_at", desc=True)  # Order by created_at instead
            .limit(limit)
            .execute()
        )
        
        users_data = users_response.data if users_response.data else []
        
        # For each user, get their persona count
        for user in users_data:
            user_id = user.get('id')
            
            # Count personas for this user
            persona_response = (
                supabase.table("main_persona")
                .select("*", count="exact")
                .eq("user_id", user_id)  # Filter by the foreign key field that references the user
                .execute()
            )
            
            user['persona_count'] = persona_response.count if persona_response.count else 0
        
        return users_data
        
    except Exception as e:
        print(f"Error fetching recent logins: {e}")
        return []