from rest_framework import serializers
from user.serializers import UserSerializer
from .models import Group, Card


class CardSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)

    class Meta:
        model = Card
        fields = ['title', 'description', 'status', 'assignee', 'start_date', 'end_date', 'priority']


class GroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'icon', 'members', 'description', 'admin']
        read_only_fields = ['admin']

class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']


class AddMemberToGroupSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
