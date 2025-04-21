from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import mixins
from django.contrib.auth import login
from .serializers import *
from group.serializers import CardSerializer, GroupSerializerForProfile
from .permissions import IsOwnerOrReadOnly
from user.models import User
from group.models import Group, Card
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class CurrentUserProfileView(generics.RetrieveAPIView, mixins.UpdateModelMixin):
    serializer_class = UserProfileSerializer
    permission_classes = [IsOwnerOrReadOnly]


    def get_object(self):
        return self.request.user

    @swagger_auto_schema(
        operation_summary="Получение профиля текущего пользователя",
        operation_description="""
        Возвращает полную информацию о профиле текущего аутентифицированного пользователя,
        включая данные пользователя, его группы и связанные карточки в каждой группе.
        """,
        responses={
            200: openapi.Response(
                description="Успешный ответ",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Данные пользователя",
                            properties={
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'groups': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Список групп пользователя с карточками",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'cards': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        description="Карточки пользователя в этой группе",
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                'title': openapi.Schema(type=openapi.TYPE_STRING),
                                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                            }
                                        )
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка запроса",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)

        columns = ColumnBoard.objects.filter(group=group)
        # Получаем карточки с предзагрузкой тегов
        cards = Card.objects.filter(group=group).prefetch_related('tags')
        cards_serializer = CardSerializer(cards, many=True)

        # Создаем словарь с информацией о колонках (имя -> цвет)
        columns_info = {col.name: {'color': col.color, 'code': col.id} for col in columns}

        # Группируем карточки по названию колонки (как было)
        grouped_cards = {}
        for column_name, column_data in columns_info.items():
            column_cards = [card for card in cards_serializer.data if card['column'] == column_name]
            grouped_cards[column_name] = {
                'name': column_name,
                'color': column_data['color'],
                'code': column_data['code'],
                'tasks': column_cards
            }

        response_data = serializer.data
        response_data['board'] = {
            'columns': list(grouped_cards.values())
        }

        return Response(response_data)
        
    @swagger_auto_schema(
        operation_summary="Обновление профиля текущего пользователя",
        operation_description="""
        Позволяет обновить данные профиля текущего пользователя.
        Для изменения пароля необходимо указать старый и новый пароль.
        """,
        request_body=UserProfileSerializer,
        responses={
            200: openapi.Response('Карточка создана', UserProfileSerializer()),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def put(self, request, *args, **kwargs):
        try:
            return self.update(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


 
class UserProfileView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            generics.GenericAPIView):
    
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'username'

    @swagger_auto_schema(
        operation_summary="Получение профиля пользователя",
        operation_description="""
        Возвращает подробную информацию о пользователе по его username.
        Включает:
        - Основные данные пользователя
        - Список групп, где состоит пользователь
        - Карточки, назначенные пользователю в каждой группе
        
        Требует аутентификации и прав доступа.
        """,
        manual_parameters=[
            openapi.Parameter(
                'username',
                openapi.IN_PATH,
                description="Уникальное имя пользователя",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешный ответ",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Данные пользователя",
                            properties={
                                'username': openapi.Schema(type=openapi.TYPE_STRING),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                            }
                        ),
                        'groups': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="Список групп пользователя с карточками",
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'cards': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        description="Карточки пользователя в этой группе",
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                'title': openapi.Schema(type=openapi.TYPE_STRING),
                                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                            }
                                        )
                                    )
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Ошибка запроса",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user_data = self.get_serializer(user).data
            
            groups = user.group_memberships.all()
            groups_data = GroupSerializerForProfile(groups, many=True).data
            
            # cards = Card.objects.filter(assignee=user)
            # cards_data = CardSerializer(cards, many=True).data

            for group, group_data in zip(groups, groups_data):
                # Фильтруем карточки пользователя в текущей группе
                cards = Card.objects.filter(group=group, assignee=user)
                # Сериализуем карточки
                group_data["cards"] = CardSerializer(cards, many=True).data
            
            response_data = {
                'user': user_data,
                'groups': groups_data,
            }

        except:
            return Response({"error": "Что то пошло не так"})
        
        return Response(response_data)

    @swagger_auto_schema(
        operation_summary="Обновление профиля пользователя",
        operation_description="""
        Обновляет данные профиля пользователя. Доступно только владельцу профиля.
        
        Особенности:
        - Для изменения пароля необходимо указать текущий пароль (old_password) и новый пароль (new_password)
        - Email и username можно менять отдельно
        - Поля, которые не нужно обновлять, можно не передавать
        """,
        request_body=UserProfileSerializer,
        manual_parameters=[
            openapi.Parameter(
                'username',
                openapi.IN_PATH,
                description="Уникальное имя пользователя",
                type=openapi.TYPE_STRING,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Успешное обновление",
                schema=UserProfileSerializer()
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING),
                        'detail': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Детали ошибок валидации по полям",
                            additional_properties=openapi.Schema(type=openapi.TYPE_STRING)
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="Доступ запрещен",
            ),
            404: openapi.Response(
                description="Пользователь не найден",
            )
        }
    )
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)


class LoginView(generics.GenericAPIView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)

        return Response({
            "message": "Login successful.",
            "username": user.username,

        })