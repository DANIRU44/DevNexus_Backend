from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import mixins
from django.contrib.auth import login
from .serializers import *
from group.serializers import CardSerializer, GroupSerializerForProfile
from .permissions import IsOwnerOrReadOnly
from user.models import User
from group.models import Group, Card


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            generics.GenericAPIView):
    
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_field = 'username'

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