def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

def get_user_agent_info(request):
    ua = request.META.get('HTTP_USER_AGENT', '')
    import httpagentparser
    info = httpagentparser.detect(ua)
    return {
        'device': info.get('platform', {}).get('name', 'Unknown'),
        'os': info.get('os', {}).get('name', 'Unknown'),
        'browser': info.get('browser', {}).get('name', 'Unknown'),
    }
