from django.http import Http404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework.exceptions import NotFound, ValidationError
from .models import Group, Card, UserTag, UserTagRelation, CardTag, ColumnBoard
from user.models import User
from .serializers import *
from .permissions import IsGroupMember
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from collections import defaultdict

error_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING)
    }
)

forbidden_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'detail': openapi.Schema(type=openapi.TYPE_STRING)
    }
)

not_found_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'detail': openapi.Schema(type=openapi.TYPE_STRING)
    }
)

class GroupCreateView(generics.CreateAPIView):
    queryset = Group.objects.all()
    permission_classes = [permissions.IsAuthenticated] 
    serializer_class = GroupCreateSerializer

    def perform_create(self, serializer):
        group = serializer.save(admin=self.request.user)
        group.members.add(self.request.user)

    def create(self, request, *args, **kwargs):

        create_serializer = self.get_serializer(data=request.data)
        create_serializer.is_valid(raise_exception=True)
        self.perform_create(create_serializer)

        output_serializer = GroupSerializer(create_serializer.instance)

        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED)


class GroupDetailView(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsGroupMember]
    lookup_field = 'group_uuid'

    @swagger_auto_schema(
        operation_summary="Получение информации о группе",
        responses={
            200: openapi.Response(
                description="Успешный ответ",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'group_uuid': openapi.Schema(type=openapi.TYPE_STRING),
                        'name': openapi.Schema(type=openapi.TYPE_STRING),
                        'icon': openapi.Schema(type=openapi.TYPE_STRING),
                        'description': openapi.Schema(type=openapi.TYPE_STRING),
                        'members': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'username': openapi.Schema(type=openapi.TYPE_STRING),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        ),
                        'board': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        'title': openapi.Schema(type=openapi.TYPE_STRING),
                                        'description': openapi.Schema(type=openapi.TYPE_STRING),
                                        'column': openapi.Schema(type=openapi.TYPE_INTEGER)
                                    }
                                )
                            )
                        )
                    }
                )
            ),
            404: openapi.Response("Группа не найдена")
        }
    )
    def get(self, request, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)

        user_tags = UserTagRelation.objects.filter(
            tag__group_id=group.group_uuid
        ).select_related('user', 'tag')

        user_tags_mapping = defaultdict(list)
        for ut in user_tags:
            user_tags_mapping[ut.user.username].append({
                'code': ut.tag.code,
                'name': ut.tag.name,
                'color': ut.tag.color
            })

        # print(user_tags_mapping)
        response_data = serializer.data

        for member in response_data['members']:
            member['tags'] = user_tags_mapping.get(member['username'], [])

        columns_queryset = ColumnBoard.objects.filter(group=group)
        columns_serializer = ColumnBoardSerializer(columns_queryset, many=True)
        columns_data = columns_serializer.data

        cards = Card.objects.filter(group=group).prefetch_related('tags')
        cards_serializer = CardSerializer(cards, many=True)
        cards_data = cards_serializer.data

        grouped_columns = []
        for column in columns_data: 
            column_cards = [
                card for card in cards_data 
                if card['column'] == column['name'] 
            ]
            grouped_columns.append({
                'name': column['name'],
                'color': column['color'],
                'code': column['id'],
                'tasks': column_cards
            })

        response_data['board'] = {'columns': grouped_columns}

        return Response(response_data)

    @swagger_auto_schema(
        operation_summary="Обновление информации о группе")
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

    def perform_update(self, serializer):
        serializer.save()


class AddMemberToGroupView(mixins.UpdateModelMixin,
                           generics.GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = AddMemberToGroupSerializer
    permission_classes = [IsGroupMember]  # Включено для продакшена
    lookup_field = 'group_uuid'

    @swagger_auto_schema(
        operation_summary="Добавление участника в группу",


operation_description="Добавляет пользователя в группу по его username"
    )
    def put(self, request, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise NotFound("User not found")

        if user in group.members.all():
            raise ValidationError({"username": "User is already a member of the group"})

        group.members.add(user)
        group.save()

        return Response({"success": "User successfully added to the group"}, status=status.HTTP_200_OK)
    

class CardCreateView(generics.CreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [IsGroupMember]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        group_uuid = self.kwargs['group_uuid']
        try:
            context['group'] = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            raise Http404("Group not found")
        return context


    @swagger_auto_schema(
        operation_summary="Создание карточки",
        operation_description="Создает новую карточку в указанной группе"
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

#тут проблемы
class CardListView(generics.GenericAPIView):
    def get_queryset(self):
        group_uuid = self.kwargs['group_uuid']
        return Card.objects.filter(group__group_uuid=group_uuid)\
            .select_related('column', 'group')\
            .prefetch_related('tags')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'cards': serializer.data})


class CardDetailView(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     mixins.DestroyModelMixin,
                     generics.GenericAPIView):
    serializer_class = CardSerializer
    lookup_field = 'code'
    permission_classes = [IsGroupMember]  # Включено для продакшена

    def get_queryset(self):
        group_uuid = self.kwargs['group_uuid']
        return Card.objects.filter(group__group_uuid=group_uuid)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        group_uuid = self.kwargs.get('group_uuid')
        try:
            context['group'] = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            raise Http404("Group not found")
        return context

    @swagger_auto_schema(operation_summary="Получение информации о карточке")
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Обновление карточки")
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Удаление карточки")
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

class UserTagDetailView(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    serializer_class = UserTagSerializer
    lookup_field = 'code'
    permission_classes = [IsGroupMember]  # Включено для продакшена

    def getueryset(self):
        group_uuid = self.kwargs['group_uuid']
        return UserTag.objects.filter(group__group_uuid=group_uuid)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        group_uuid = self.kwargs.get('group_uuid')
        try:
            context['group'] = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            raise Http404("Group not found")
        return context

    @swagger_auto_schema(operation_summary="Получение информации о теге для пользователей")
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Обновление тега для пользователей")
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Удаление тега для пользователей")
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UserTagCreateView(generics.CreateAPIView):
    serializer_class = UserTagCreateSerializer

    @swagger_auto_schema(
        operation_summary="Создание тега для пользователей",
        operation_description="Создает новый тег для пользователей для указанной группы")
    def create(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            return Response({"error": "Группа не найдена."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data['name']
        color = serializer.validated_data['color']

        if UserTag.objects.filter(name=name, color=color, group=group).exists():
            return Response({"error": "Такой тег уже существует в этой группе."}, status=status.HTTP_400_BAD_REQUEST)

        instance = UserTag.objects.create(
            group=group,
            **serializer.validated_data
        )

        response_serializer = UserTagSerializer(instance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class UserTagListView(generics.GenericAPIView):
    serializer_class = UserTagSerializer

    def get_queryset(self, group_uuid):
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            return UserTag.objects.filter(group=group)
        except Group.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        tags = self.get_queryset(group_uuid)

        if tags is None:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
    

class UserTagDetailView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   generics.GenericAPIView):
    queryset = UserTag.objects.all()
    serializer_class = UserTagSerializer
    lookup_field = 'code' 

    @swagger_auto_schema(
        operation_summary="Получение информации о теге для пользователей")
    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = UserTag.objects.get(code=code, group=group)
            serialized_usertag = UserTagSerializer(tag)

            return Response(serialized_usertag.data) 
        
        except UserTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Обновление тега для пользователей")
    def put(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = UserTag.objects.get(code=code, group=group)
            return self.update(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except UserTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Удаление тега для пользователей")
    def delete(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = UserTag.objects.get(code=code, group=group)
            tag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except UserTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)
        

class UserTagRelationCreateView(generics.CreateAPIView):
    serializer_class = UserTagRelationSerializer

    @swagger_auto_schema(
        operation_summary="Создание связи пользователя с тегом",
        operation_description="Создает связь между пользователем и тегом в указанной группе"
    )
    def create(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            return Response(
                {"error": "Группа не найдена."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(data=request.data)
        serializer.context['group'] = group
        serializer.is_valid(raise_exception=True)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class UserTagRelationDeleteView(generics.DestroyAPIView):
    serializer_class = UserTagRelationSerializer

    @swagger_auto_schema(
        operation_summary="Удаление связи пользователя с тегом",
        operation_description="Удаляет связь между пользователем и тегом в указанной группе"
    )
    def delete(self, request, group_uuid, username, tag_code, *args, **kwargs):
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            user = User.objects.get(username=username, group=group)
            tag = UserTag.objects.get(code=tag_code, group=group)
            user_tag = UserTagRelation.objects.get(user=user, tag=tag)
            user_tag.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        except Group.DoesNotExist:
            return Response(
                {"error": "Группа не найдена."},
                status=status.HTTP_404_NOT_FOUND)
        
        except User.DoesNotExist:
            return Response(
                {"error": "Пользователь не найден в группе."},
                status=status.HTTP_404_NOT_FOUND)
        
        except UserTag.DoesNotExist:
            return Response(
                {"error": "Тег не найден в группе."},
                status=status.HTTP_404_NOT_FOUND)
        
        except UserTagRelation.DoesNotExist:
            return Response(
                {"error": "Связь не найден в группе."},
                status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class GroupCardTagCreateView(generics.CreateAPIView):
    serializer_class = GroupCardTagCreateSerializer

    @swagger_auto_schema(
        operation_summary="Создание тега для карточек группы",
        operation_description="Создает новый тег для карточек в указанной группе")
    def create(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            return Response({"error": "Группа не найдена."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data['name']
        color = serializer.validated_data['color']

        if CardTag.objects.filter(name=name, color=color, group=group).exists():
            raise ValidationError({"error": "Такой тег уже существует в этой группе."})

        self.perform_create(serializer, group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, group):
        serializer.save(group=group)


class GroupCardTagListView(generics.GenericAPIView):
    serializer_class = GroupCardTagSerializer

    def get_queryset(self, group_uuid):
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            return CardTag.objects.filter(group=group)
        except Group.DoesNotExist:
            return None

    @swagger_auto_schema(
        operation_summary="Получение списка тегов карточек группы",
        operation_description="Возвращает все теги карточек для указанной группы")
    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        tags = self.get_queryset(group_uuid)

        if tags is None:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class GroupCardTagDetailView(mixins.RetrieveModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             generics.GenericAPIView):
    serializer_class = GroupCardTagSerializer
    lookup_field = 'code'
    permission_classes = [IsGroupMember]  # Включено для продакшена

    def get_queryset(self):
        group_uuid = self.kwargs['group_uuid']
        return CardTag.objects.filter(group__group_uuid=group_uuid)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        group_uuid = self.kwargs.get('group_uuid')
        try:
            context['group'] = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            raise Http404("Group not found")
        return context

    @swagger_auto_schema(operation_summary="Получение информации о теге карточек")
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Обновление тега карточек")
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Удаление тега карточек")
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)

        

class ColumnBoardCreateView(generics.CreateAPIView):
    serializer_class = ColumnBoardSerializer

    @swagger_auto_schema(
        operation_summary="Создание колонки")
    def create(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            return Response({"error": "Группа не найдена."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data['name']
        color = serializer.validated_data['color']

        if ColumnBoard.objects.filter(name=name, color=color, group=group).exists():
            raise ValidationError({"error": "Такая колонка уже существует в этой группе."})

        self.perform_create(serializer, group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, group):
        serializer.save(group=group)


class ColumnBoardDetailView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.DestroyModelMixin,
                            generics.GenericAPIView):
    serializer_class = ColumnBoardSerializer
    lookup_field = 'id'
    permission_classes = [IsGroupMember]  # Включено для продакшена

    def get_queryset(self):
        group_uuid = self.kwargs['group_uuid']
        return ColumnBoard.objects.filter(group__group_uuid=group_uuid)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        group_uuid = self.kwargs.get('group_uuid')
        try:
            context['group'] = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            raise Http404("Group not found")
        return context

    @swagger_auto_schema(operation_summary="Получение информации о колонке")
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Обновление колонки")
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(operation_summary="Удаление колонки")
    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)