from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LoginView, MeViewSet, RefreshView, SkillViewSet, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")
router.register("skills", SkillViewSet, basename="skills")

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshView.as_view(), name="token_refresh"),
    path("me/", MeViewSet.as_view({"get": "me"}), name="me"),
    path("", include(router.urls)),
]
