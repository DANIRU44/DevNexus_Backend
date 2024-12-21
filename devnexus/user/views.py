from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import mixins
from django.contrib.auth import login
from .serializers import *
from group.serializers import CardSerializer, GroupSerializer
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
            groups_data = GroupSerializer(groups, many=True).data
            
            cards = Card.objects.filter(assignee=user)
            cards_data = CardSerializer(cards, many=True).data
            
            response_data = {
                'user': user_data,
                'groups': groups_data,
                'cards': cards_data,
            }
        except:
            return Response({"error": "Что то пошло не так"})
        
        return Response(response_data)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    # def put(self, request, username):
    #     try:
    #         user = User.objects.get(username=username)
    #     except User.DoesNotExist:
    #         return Response({"error": "User  not found"}, status=404)
        
    #     self.check_object_permissions(request, user)
    #     serializer = UserProfileSerializer(user, data=request.data)

    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=200)
    #     return Response(serializer.errors, status=400)



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