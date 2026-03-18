from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    UsuarioViewSet,
    MototaxiViewSet,
    ViajeViewSet,
    PagoViewSet,
    OfertaViewSet,
    RegistroUsuarioAPIView,
    UsuarioActualAPIView,
    CustomTokenObtainPairView,
)

from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('usuarios', UsuarioViewSet)
router.register('mototaxis', MototaxiViewSet)
router.register('viajes', ViajeViewSet)
router.register('pagos', PagoViewSet)
router.register('ofertas', OfertaViewSet)

urlpatterns = [
    # Usuario autenticado
    path('usuario/', UsuarioActualAPIView.as_view(), name='usuario_actual'),

    path("usuarios/registro/", RegistroUsuarioAPIView.as_view(), name="registro"),

    # Autenticación JWT
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Endpoints del sistema
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
