# login/permissions.py
from rest_framework import permissions
from .models import Blocklist


class BlocklistPermission(permissions.BasePermission):
    """
    Global permission check for blocked IPs.
    """

    def has_permission(self, request, view):
        ip_addr = self.get_client_ip(request)
        
        print(f"DEBUG: Checking IP: {ip_addr}")  # Console output
        
        blocked = Blocklist.objects.filter(
            ip_addr=ip_addr, 
            is_active=True
        ).exists()
        
        print(f"DEBUG: IP {ip_addr} blocked: {blocked}")
        
        return not blocked

    def get_client_ip(self, request):
        """Get the client's IP address, handling proxies."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        print(f"DEBUG: Raw IP detection - X-Forwarded-For: {x_forwarded_for}, REMOTE_ADDR: {request.META.get('REMOTE_ADDR')}")
        return ip