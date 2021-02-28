from django.urls import include, path

from dynamic_rest.routers import DynamicRouter

from .apiviews import UserViewSet


router = DynamicRouter()
router.register('users', UserViewSet)

urlpatterns = [
    path('', include(router.urls))
]
