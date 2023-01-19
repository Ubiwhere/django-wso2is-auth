from rest_framework.routers import DefaultRouter

from .views import GetTokenAPIView, RefreshTokenAPIView

router = DefaultRouter()
router.register("auth/token", GetTokenAPIView.as_view())
router.register("auth/token/refresh", RefreshTokenAPIView.as_view())

urlpatterns = router.urls
