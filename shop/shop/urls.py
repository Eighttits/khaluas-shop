from django.urls import include, path
from rest_framework import routers
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core import views

router = routers.DefaultRouter()
# router.register(r'users', views.UserCreateView)
router.register(r'groups', views.GroupViewSet)
router.register(r'categories', views.CategoryViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'resource-images', views.ResourceImageViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'orders', views.OrderViewSet)
router.register(r'order-items', views.OrderItemViewSet)
router.register(r'carts', views.CartViewSet)
router.register(r'cart-items', views.CartItemViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('create-user/', views.UserCreateView.as_view(), name='create-user'),
    path('trending-products/', views.TrendingProductListView.as_view(), name='trending-products'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('check-email/', views.CheckEmailView.as_view(), name='check-email'),
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('api/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/user/', views.UserInfoView.as_view(), name='user-info'),
    path('api/verify-token/', views.verify_token, name='verify-token'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)