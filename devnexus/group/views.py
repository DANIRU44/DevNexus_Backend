from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework import mixins
from .models import Group, Card
from user.models import User
from .serializers import GroupSerializer, GroupCreateSerializer, AddMemberToGroupSerializer, CardSerializer
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
    permission_classes = [IsGroupMember]
    lookup_field = 'group_uuid'

    def get(self, request, *args, **kwargs):
        group = self.get_object()
        serializer = self.get_serializer(group)

        cards = Card.objects.filter(group=group)
        cards_serializer = CardSerializer(cards, many=True)

        # Сортируем карточки 
        grouped_cards = {
            'todo': [],
            'in_progress': [],
            'done': []
        }

        for card in cards_serializer.data:
            status = card['status']
            if status in grouped_cards:
                grouped_cards[status].append(card)

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
    permission_classes = [IsGroupMember]
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

    def perform_create(self, serializer):
        group_uuid = self.kwargs['group_uuid']
        group = Group.objects.get(group_uuid=group_uuid)
        serializer.save(group=group)


class CardListView(generics.GenericAPIView):
    serializer_class = CardSerializer
    lookup_field = 'code'

    def get(self, request, *args, **kwargs):
        group_uuid = self.kwargs['group_uuid']
        group = Group.objects.get(group_uuid=group_uuid)
        cards = Card.objects.filter(group=group)
        cards_serializer = CardSerializer(cards, many=True)

        grouped_cards = {
            'todo': [],
            'in_progress': [],
            'done': []
        }

        for card in cards_serializer.data:
            status = card['status']  # Получаем статус карточки
            if status in grouped_cards:
                grouped_cards[status].append(card)  # Добавляем карточку в соответствующий 

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



