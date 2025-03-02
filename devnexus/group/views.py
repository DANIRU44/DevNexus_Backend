from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from rest_framework.exceptions import NotFound, ValidationError
from .models import Group, Card, GroupTag, UserTag, CardTag, ColumnBoard
from user.models import User
from .serializers import *
from .permissions import IsGroupMember


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