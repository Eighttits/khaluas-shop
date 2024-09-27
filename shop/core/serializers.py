from django.contrib.auth.models import Group, User
from rest_framework import serializers
from core.models import Category, Product, Comment, Order, OrderItem, Cart, CartItem, ResourceImage
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .model import classify_comment

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)

        # Aquí agregamos la información adicional que queremos incluir
        data['is_staff'] = self.user.is_staff

        return data

class UserSerializer(serializers.ModelSerializer):
    is_staff = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_staff']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_is_staff(self, value):
        # Verifica si el usuario actual es un administrador
        if self.context['request'].user.is_authenticated and self.context['request'].user.is_staff:
            return value
        # Si no es administrador, siempre retorna False
        return False

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            is_staff=validated_data.get('is_staff', False)  # Garantiza que solo los admins puedan establecer is_staff
        )
        return user

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image']

class ProductSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'category', 'image', 'created_at']
        
class ResourceImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceImage
        fields = ['id', 'name', 'image']

# class CommentSerializer(serializers.ModelSerializer):
#     user = serializers.StringRelatedField(read_only=True)  # Show username
#     product = serializers.StringRelatedField(read_only=True)

#     class Meta:
#         model = Comment
#         fields = ['id', 'user', 'product', 'text', 'rating', 'created_at']

# class CommentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Comment
#         fields = ['id', 'product', 'text', 'rating', 'created_at', 'user']  # Excluye 'user'
#         extra_kwargs = {
#             'user': {'required': False}
#         }

#     def validate(self, data):
#         if not data.get('product'):
#             raise serializers.ValidationError({"product": "This field is required."})
#         if not data.get('text'):
#             raise serializers.ValidationError({"text": "This field is required."})
#         if not data.get('rating') or data['rating'] < 0:
#             raise serializers.ValidationError({"rating": "Invalid rating. Must be a non-negative integer."})
#         return data

class CommentSerializer(serializers.ModelSerializer):
    sentiment = serializers.SerializerMethodField()  # Campo añadido para el sentimiento

    class Meta:
        model = Comment
        fields = ['id', 'product', 'text', 'rating', 'created_at', 'user', 'sentiment']
        extra_kwargs = {
            'user': {'required': False}
        }

    def validate(self, data):
        if not data.get('product'):
            raise serializers.ValidationError({"product": "This field is required."})
        if not data.get('text'):
            raise serializers.ValidationError({"text": "This field is required."})
        if not data.get('rating') or data['rating'] < 0:
            raise serializers.ValidationError({"rating": "Invalid rating. Must be a non-negative integer."})
        return data

    def get_sentiment(self, obj):
        return classify_comment(obj.text)  # Usa la función de clasificación para determinar el sentimiento


class OrderItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), source='product')

    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    user = serializers.ReadOnlyField(source='user.username')  # Mostrar solo para lectura

    class Meta:
        model = Order
        fields = ['id', 'user', 'total_price', 'status', 'created_at', 'items']
        extra_kwargs = {
            'total_price': {'required': False},
            'items': {'required': False}
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        return order

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True) 
    cart = serializers.PrimaryKeyRelatedField(queryset=Cart.objects.all(), write_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'cart']



class CartSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'items']
