from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework.exceptions import NotFound, ValidationError
from .models import Group, Card, GroupTag, UserTag, CardTag, ColumnBoard
from user.models import User
from .serializers import *
from .permissions import IsGroupMember
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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


class GroupDetailView(mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin,
                      mixins.DestroyModelMixin,
                      generics.GenericAPIView):
    
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    # permission_classes = [IsGroupMember] отключу на время тестирования
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

        columns = ColumnBoard.objects.filter(group=group)
        cards = Card.objects.filter(group=group)

        cards_serializer = CardSerializer(cards, many=True)

        grouped_cards = {}
        for column in columns:
            column_cards = [card for card in cards_serializer.data if card['column'] == column.id]
            grouped_cards[column.name] = column_cards

        response_data = serializer.data
        response_data['board'] = grouped_cards

        return Response(response_data)

    @swagger_auto_schema(
        operation_summary="Обновление информации о группе")
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    # def get_object(self):
    #     # Переопределяем метод для получения группы по group_uuid
    #     group_uuid = self.kwargs.get('group_uuid')
    #     return get_object_or_404(Group, group_uuid=group_uuid)

    def perform_update(self, serializer):
        serializer.save()


class AddMemberToGroupView(mixins.UpdateModelMixin,
                            generics.GenericAPIView):
    queryset = Group.objects.all()
    serializer_class = AddMemberToGroupSerializer
    # permission_classes = [IsGroupMember] отключу на время тестирования
    lookup_field = 'group_uuid'
    
    # def get_object(self):
    #     # Переопределяем метод для получения группы по group_uuid
    #     group_uuid = self.kwargs.get('group_uuid')
    #     return get_object_or_404(Group, group_uuid=group_uuid)
    
    @swagger_auto_schema(
        operation_summary="Добавление участника в группу",
        operation_description="Добавляет пользователя в группу по его username")
    def put(self, request, *args, **kwargs):
            group = self.get_object()
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            username = serializer.validated_data['username']

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)

            if user in group.members.all():
                return Response({"error": "Пользователь уже является участником группы."}, status=status.HTTP_400_BAD_REQUEST)

            group.members.add(user)
            group.save()


class CardCreateView(generics.CreateAPIView):
    serializer_class = CardSerializer
    lookup_field = 'code'

    @swagger_auto_schema(
        operation_summary="Создание карточки",
        operation_description="Создает новую карточку в указанной группе")
    def create(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
        except Group.DoesNotExist:
            return Response({"error": "Группа не найдена."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer, group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, group):
        serializer.save(group=group)


class CardListView(generics.GenericAPIView):
    serializer_class = CardSerializer
    lookup_field = 'code'

    def get(self, request, *args, **kwargs):

        group_uuid = self.kwargs['group_uuid']
        group = Group.objects.get(group_uuid=group_uuid)

        columns = ColumnBoard.objects.filter(group=group)

        cards = Card.objects.filter(group=group)
        cards_serializer = CardSerializer(cards, many=True)

        grouped_cards = {}
        for column in columns:
            column_cards = [card for card in cards_serializer.data if card['column'] == column.id]
            grouped_cards[column.name] = column_cards

        return Response(grouped_cards)


class CardDetailView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   generics.GenericAPIView):
    serializer_class = CardSerializer
    lookup_field = 'code'
    queryset = Card.objects.all()

    @swagger_auto_schema(
        operation_summary="Получение информации о карточке")
    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            card = Card.objects.get(code=code, group=group)
            serialized_card = CardSerializer(card)

            return Response(serialized_card.data) 
        
        except Card.DoesNotExist:
            return Response({"error": "Такой карточки не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Обновление карточки")
    def put(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            card = Card.objects.get(code=code, group=group)
            return self.update(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Card.DoesNotExist:
            return Response({"error": "Такой карточки не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Удаление карточки")
    def delete(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
            card = Card.objects.get(code=code, group=group)
            return self.destroy(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Card.DoesNotExist:
            return Response({"error": "Такой карточки не существует"}, status=status.HTTP_404_NOT_FOUND)


class GroupTagCreateView(generics.CreateAPIView):
    serializer_class = GroupTagCreateSerializer

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

        if GroupTag.objects.filter(name=name, color=color, group=group).exists():
            raise ValidationError({"error": "Такой тег уже существует в этой группе."})

        self.perform_create(serializer, group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer, group):
        serializer.save(group=group)


class GroupTagListView(generics.GenericAPIView):
    serializer_class = GroupTagSerializer

    def get_queryset(self, group_uuid):
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            return GroupTag.objects.filter(group=group)
        except Group.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        tags = self.get_queryset(group_uuid)

        if tags is None:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)
    

class GroupTagDetailView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   generics.GenericAPIView):
    queryset = GroupTag.objects.all()
    serializer_class = GroupTagSerializer
    lookup_field = 'code' 

    @swagger_auto_schema(
        operation_summary="Получение информации о теге для пользователей")
    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = GroupTag.objects.get(code=code, group=group)
            serialized_grouptag = GroupTagSerializer(tag)

            return Response(serialized_grouptag.data) 
        
        except GroupTag.DoesNotExist:
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
            tag = GroupTag.objects.get(code=code, group=group)
            return self.update(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except GroupTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Удаление тега для пользователей")
    def delete(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = GroupTag.objects.get(code=code, group=group)
            return self.destroy(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except GroupTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)
        

class UserTagCreateView(generics.CreateAPIView):
    queryset = UserTag.objects.all()
    serializer_class = UserTagSerializer

    @swagger_auto_schema(
        operation_summary="Создание связи пользователя с тегом",
        operation_description="Создает связь между пользователем и тегом")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username=serializer.validated_data['username']
        tag=serializer.validated_data['tag']

        if UserTag.objects.filter(username=username, tag=tag).exists():
            raise ValidationError("Связь между пользователем и тегом уже существует.")

        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserTagDeleteView(generics.DestroyAPIView):
    queryset = UserTag.objects.all()
    serializer_class = UserTagSerializer

    @swagger_auto_schema(
        operation_summary="Удаление связи пользователя с тегом",
        operation_description="Удаляет связь между пользователем и тегом")
    def delete(self, request, username, tag, *args, **kwargs):
        # Пытаемся найти объект UserTag по username и tag
        try:
            instance = UserTag.objects.get(username=username, tag=tag)
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except UserTag.DoesNotExist:
            raise NotFound("Связь не найдена.")
        

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
    queryset = CardTag.objects.all()
    serializer_class = GroupCardTagSerializer
    lookup_field = 'code' 

    @swagger_auto_schema(
        operation_summary="Получение информации о теге карточек")
    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = CardTag.objects.get(code=code, group=group)
            serialized_grouptag = GroupCardTagSerializer(tag)

            return Response(serialized_grouptag.data) 
        
        except CardTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Обновление тега карточек")
    def put(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = CardTag.objects.get(code=code, group=group)
            return self.update(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except CardTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Удаление тега карточек")
    def delete(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        code = self.kwargs['code']

        try:
            group = Group.objects.get(group_uuid=group_uuid)
            tag = CardTag.objects.get(code=code, group=group)
            return self.destroy(request, *args, **kwargs)
        
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)
        except CardTag.DoesNotExist:
            return Response({"error": "Такого тега не существует"}, status=status.HTTP_404_NOT_FOUND)
        

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
    queryset = ColumnBoard.objects.all()
    serializer_class = ColumnBoardSerializer
    lookup_field = 'id'  # Используем 'id' вместо 'code', так как в модели ColumnBoard нет поля 'code'

    @swagger_auto_schema(
        operation_summary="Получение информации о колонке")
    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        column_id = self.kwargs['id']  # Используем 'id' вместо 'code'
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            column = ColumnBoard.objects.get(id=column_id, group=group)
            serialized_column = ColumnBoardSerializer(column)
            return Response(serialized_column.data)
        
        except ColumnBoard.DoesNotExist:
            return Response({"error": "Такой колонки не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_summary="Обновление колонки")
    def put(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        column_id = self.kwargs['id']  # Используем 'id' вместо 'code'
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            column = ColumnBoard.objects.get(id=column_id, group=group)
            serializer = self.get_serializer(column, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        except ColumnBoard.DoesNotExist:
            return Response({"error": "Такой колонки не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(operation_summary="Удаление колонки")
    def delete(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        column_id = self.kwargs['id']  # Используем 'id' вместо 'code'
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            column = ColumnBoard.objects.get(id=column_id, group=group)
            column.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        except ColumnBoard.DoesNotExist:
            return Response({"error": "Такой колонки не существует"}, status=status.HTTP_404_NOT_FOUND)
        except Group.DoesNotExist:
            return Response({"error": "Такой группы не существует"}, status=status.HTTP_404_NOT_FOUND)