from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    UsuarioViewSet,
    MototaxiViewSet,
    ViajeViewSet,
    PagoViewSet,
    OfertaViewSet,
    DestinoViewSet,
    RegistroUsuarioAPIView,
    UsuarioActualAPIView,
    CustomTokenObtainPairView,
    ChangePasswordView,
    check_version,
    
)

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet)
router.register('mototaxis', MototaxiViewSet)
router.register('viajes', ViajeViewSet)
router.register('pagos', PagoViewSet)
router.register('ofertas', OfertaViewSet)
router.register('destino', DestinoViewSet)

urlpatterns = [
    # Usuario autenticado
    path('usuario/', UsuarioActualAPIView.as_view(), name='usuario_actual'),

    path("usuarios/registro/", RegistroUsuarioAPIView.as_view(), name="registro"),
    
    path('usuarios/cambiar-password/', ChangePasswordView.as_view(), name='cambiar-password'),

    # Autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('check_version/', check_version, name='check_version'),

    # Endpoints del sistema
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
