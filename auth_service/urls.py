from django.urls import path
from .views.auth_views import login_view, callback_view, logout_view, redirect_view
from .views.user_views import me, permissions

app_name = 'auth_service'

urlpatterns = [
    path('login/<str:provider>/', login_view, name='login'),
    path('callback/<str:provider>/', callback_view, name='callback'),
    path('logout/', logout_view, name='logout'),
    path('redirect/', redirect_view, name='redirect'),
    path('me/', me, name='me'),
    path('permissions/', permissions, name='permissions'),
]