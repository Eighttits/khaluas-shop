from django.contrib.auth.models import Group, User
from rest_framework import permissions, viewsets, generics, filters
from core.models import Category, Product, Comment, Order, OrderItem, Cart, CartItem, ResourceImage
from core.serializers import (
    CategorySerializer,
    ProductSerializer,
    CommentSerializer,
    OrderSerializer,
    OrderItemSerializer,
    CartSerializer,
    CartItemSerializer,
    GroupSerializer, 
    UserSerializer,
    CustomTokenObtainPairSerializer,
    ResourceImageSerializer
)
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from core.permissions import IsAdminUserOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.middleware.csrf import get_token
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import TokenObtainPairView
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from django_filters.rest_framework import DjangoFilterBackend


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """
    Endpoint para verificar la validez de un token.
    """
    try:
        # Aquí puedes verificar el token con el servidor externo si es necesario
        # Por ejemplo, podrías hacer una petición al servidor de autenticación si es necesario
        user = request.user  # Obtenemos el usuario autenticado

        # Si el usuario está autenticado, el token es válido
        return Response({'valid': True, 'username': user.username}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'valid': False, 'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@api_view(['POST'])
def add_to_cart(request):
    try:
        data = request.data
        cart_id = data.get('cart')
        product_id = data.get('product')
        quantity = data.get('quantity')

        # Verificar que el carrito y el producto existen
        cart = Cart.objects.get(id=cart_id)
        product = Product.objects.get(id=product_id)

        # Crear o actualizar el ítem del carrito
        cart_item, created = CartItem.objects.update_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Cart.DoesNotExist:
        return Response({"error": "Cart not found"}, status=status.HTTP_404_NOT_FOUND)
    except Product.DoesNotExist:
        return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_csrf_token(request):
    csrf_token = get_token(request)
    return JsonResponse({'csrfToken': csrf_token})

class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CheckEmailView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email', None)
        
        if email is None:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({"isRegistered": True})
        else:
            return Response({"isRegistered": False})


class UserCreateView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [AllowAny] 

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all().order_by('name')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
class TrendingProductListView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def perform_destroy(self, instance):
        if instance.image:
            if default_storage.exists(instance.image.path):
                default_storage.delete(instance.image.path)
        instance.delete()

    def perform_update(self, serializer):
        instance = serializer.save()
        previous_instance = self.get_object()

        # Check if a new image was uploaded
        if 'image' in self.request.data:
            previous_image = previous_instance.image
            if previous_image and previous_image != instance.image:
                if default_storage.exists(previous_image.path):
                    default_storage.delete(previous_image.path)
                    
                    
class ResourceImageViewSet(viewsets.ModelViewSet):
    queryset = ResourceImage.objects.all()
    serializer_class = ResourceImageSerializer
    permission_classes = [IsAdminUserOrReadOnly]

# class CommentViewSet(viewsets.ModelViewSet):
#     queryset = Comment.objects.all()
#     serializer_class = CommentSerializer
    
#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']

    def update(self, request, *args, **kwargs):
        partial = True  # Allows partial updates
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            print("Validation errors:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()  # Staff can see all orders
        return Order.objects.filter(user=user)  # Non-staff users see only their orders

    def perform_update(self, serializer):
        serializer.save()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        

class CartItemViewSet(viewsets.ModelViewSet):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)
    
# class CartViewSet(viewsets.ModelViewSet):
#     serializer_class = CartSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Cart.objects.filter(user=self.request.user)

# class CartItemViewSet(viewsets.ModelViewSet):
#     serializer_class = CartItemSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return CartItem.objects.filter(cart__user=self.request.user)