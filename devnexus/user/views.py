from rest_framework import generics, permissions
from rest_framework.response import Response
from django.contrib.auth import login
from .serializers import UserSerializer
from user.models import User

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]