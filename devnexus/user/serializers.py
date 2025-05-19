from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.core import exceptions
from user.models import User
import re


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user
    

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'description']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'description': {'required': False},
        }

    def update(self, instance, validated_data):
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        validators=[validate_password]
    )

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Неверный текущий пароль")
        return value

    def validate_new_password(self, value):

        errors = []
    # Проверки всякие
        if len(value) < 8:
            errors.append("Пароль должен содержать минимум 8 символов")

        if not re.findall(r'\d', value):
            errors.append("Пароль должен содержать минимум 1 цифру")

        if not re.findall(r'[A-Z]', value):
            errors.append("Пароль должен содержать минимум 1 заглавную букву")
            
        if not re.findall(r'[a-z]', value):
            errors.append("Пароль должен содержать минимум 1 строчную букву")
            

        if not re.findall(r'[!@#$%^&*()\-_=+{};:,<.>/?]', value):
            errors.append("Пароль должен содержать минимум 1 специальный символ")

        if errors:
            raise serializers.ValidationError(errors)
    # --------------------------------------

        try:
            validate_password(value)
        except exceptions.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)
        if user is None:
            raise serializers.ValidationError('Не правильный юзернейм или пароль')

        attrs['user'] = user
        return attrs
    

