from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES, default='immediate')
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    store_name = serializers.CharField(required=False, allow_blank=True)
    business_address = serializers.CharField(required=False, allow_blank=True)
    tax_id = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 'phone',
            'password', 'password2', 'user_type', 'store_name',
            'business_address', 'tax_id', 'location', 'date_of_birth'
        ]
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        
        user_type = data.get('user_type', 'immediate')
        
        # Only require store_name for bulk sellers
        if user_type == 'bulk' and not data.get('store_name', '').strip():
            raise serializers.ValidationError({"store_name": "Store name is required for bulk sellers"})
        
        if not data.get('username'):
            data['username'] = data['email'].split('@')[0]
            base = data['username']
            counter = 1
            while User.objects.filter(username=data['username']).exists():
                data['username'] = f"{base}{counter}"
                counter += 1
        
        return data
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user_type = validated_data.pop('user_type')
        password = validated_data.pop('password')
        
        # Remove empty string values and keep only non-empty values
        validated_data = {k: v for k, v in validated_data.items() if v and (isinstance(v, bool) or str(v).strip())}
        
        user = User.objects.create_user(password=password, user_type=user_type, **validated_data)
        if user_type == 'bulk':
            user.is_verified_seller = False
            user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(request=self.context.get('request'), username=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled")
        data['user'] = user
        return data

class UserDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'store_name', 'business_address', 'tax_id',
            'is_verified_seller', 'profile_picture', 'location', 'date_of_birth',
            'created_at'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name()