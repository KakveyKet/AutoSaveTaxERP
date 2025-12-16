from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    UserViewSet, ForwarderViewSet, DestinationViewSet, 
    OrderImportViewSet, RegisterView, say_hello, dashboard_stats, MyTokenObtainPairView, SecretAdminRecoveryView
)

router = DefaultRouter()
# ERROR FIX: Added basename='user' because UserViewSet uses get_queryset instead of queryset
router.register(r'users', UserViewSet, basename='user') 
router.register(r'forwarders', ForwarderViewSet)
router.register(r'destinations', DestinationViewSet)
router.register(r'orders', OrderImportViewSet, basename='orderimport')

urlpatterns = [
    # Auth
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('secret-recovery/', SecretAdminRecoveryView.as_view(), name='secret_recovery'),

    # API Routes
    path('', include(router.urls)),
    
    # Dashboard Stats Route
    path('dashboard/stats/', dashboard_stats, name='dashboard_stats'),
    
    # Settings Route
    # path('system/settings/', SystemSettingView.as_view(), name='system_settings'),

    # Test
    path('hello/', say_hello, name='hello'),
]