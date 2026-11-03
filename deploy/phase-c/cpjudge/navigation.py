def contest_navigation(request):
    from judge.models import NavigationBar
    # No standalone archive, practice, editorials, virtual or announcements.
    from .models import Identity
    return {'nav_bar':NavigationBar.objects.filter(path='/contests/'),
            'cpj_can_author': bool(request.user.is_authenticated and request.user.is_active and Identity.objects.filter(user=request.user,is_author=True).exists())}
