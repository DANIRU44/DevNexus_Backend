from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import mixins, status
from django.contrib.auth import login
from .serializers import *
from group.serializers import CardSerializer, GroupSerializerForProfile, UserTagRelationSerializer
from .permissions import IsOwnerOrReadOnly
from user.models import User
from group.models import Group, Card, UserTagRelation, UserTag
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_summary="Регистрация пользователя",
        operation_description="""
        Создает нового пользователя. Пароль должен содержать:
        - Минимум 8 символов
        - Цифру
        - Заглавную и строчную букву
        - Специальный символ
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Пароль (минимум 8 символов, цифра, заглавная и строчная буква, спецсимвол)"
                )
            }
        ),
        responses={
            201: openapi.Response(
                description="Пользователь создан",
                schema=UserSerializer
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING)
                            )
                        )
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {"status": "Пользователь успешно зарегистрирован"},
                status=status.HTTP_201_CREATED
            )
        
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


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
                                                'column': openapi.Schema(type=openapi.TYPE_STRING),
                                                'column_color': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                description="Цвет колонки"
                                            ),
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

        except Exception as e:
            return Response({"error": str(e)}, status=400)
        
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

        except Exception as e:
            return Response({"error": str(e)}, status=400)
        
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
    

class ChangePasswordView(APIView):
    permission_classes = [IsOwnerOrReadOnly]
    
    @swagger_auto_schema(
        operation_summary="Смена пароля",
        operation_description="""
        Изменяет пароль текущего пользователя.
        Требует аутентификации и проверки старого пароля.
        Новый пароль должен содержать:
        - Минимум 8 символов
        - Цифру
        - Заглавную и строчную букву
        - Специальный символ
        """,
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password'],
            properties={
                'old_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Текущий пароль"
                ),
                'new_password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_PASSWORD,
                    description="Новый пароль (минимум 8 символов, цифра, заглавная и строчная буква, спецсимвол)"
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Пароль успешно изменен",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={'status': openapi.Schema(type=openapi.TYPE_STRING)}
                )
            ),
            400: openapi.Response(
                description="Ошибка валидации",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(type=openapi.TYPE_STRING)
                            )
                        )
                    }
                )
            )
        }
    )
    def put(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # update_session_auth_hash(request, user)
            
            return Response(
                {"status": "Пароль успешно изменен"},
                status=status.HTTP_200_OK
            )
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileGroupView(mixins.RetrieveModelMixin,generics.GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    # permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'username'

    @swagger_auto_schema(
        operation_summary="Получение профиля пользователя по конкретной группе",
        operation_description="""
        Получает данные профиля пользователя по конкретной группе.""")
    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()

            group_uuid = self.kwargs['group_uuid']
            group = Group.objects.get(group_uuid=group_uuid)

            cards = Card.objects.filter(group=group, assignee=user)
            cards_data = CardSerializer(cards, many=True).data

            # Вручную сериализуем теги пользователя, я не знаю почему не работает
            user_tags = UserTagRelation.objects.filter(
                user=user,
                tag__group=group
            ).select_related('tag')

            user_tags_data = [
                {
                    "tag_code": ut.tag.code,
                    "tag_name": ut.tag.name,
                    "tag_color": ut.tag.color
                }
                for ut in user_tags
            ]

            return Response({
                "user": UserProfileSerializer(user).data,
                "user_tags": user_tags_data,
                "cards": cards_data
            })
        except Exception as e:
            return Response({"error": str(e)}, status=400)


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