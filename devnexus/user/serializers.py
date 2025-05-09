from rest_framework import serializers
from django.contrib.auth import authenticate
from user.models import User


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
    old_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
    new_password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        max_length=128
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'old_password', 'new_password', 'description']
        extra_kwargs = {
            'username': {'required': False},
            'email': {'required': False},
            'description': {'required': False},
        }

    def validate(self, data):
        # Проверяем, что новый пароль не пустой, если передан
        if 'new_password' in data and data['new_password'] == '':
            raise serializers.ValidationError("Новый пароль не может быть пустым")
        return data

    def update(self, instance, validated_data):
        # Извлекаем пароли из данных
        old_password = validated_data.pop('old_password', None)
        new_password = validated_data.pop('new_password', None)

        # Если пытаемся изменить пароль
        if new_password:
            if not old_password:
                raise serializers.ValidationError("Для изменения пароля укажите текущий пароль")
            
            if not instance.check_password(old_password):
                raise serializers.ValidationError("Неверный текущий пароль")
            
            instance.set_password(new_password)

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


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
    

