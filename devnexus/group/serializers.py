from rest_framework import serializers
from user.serializers import UserSerializer
from .models import Group, Card, GroupTag


class CardSerializer(serializers.ModelSerializer):
    assignee = UserSerializer()

    class Meta:
        model = Card
        fields = ['title', 'description', 'status', 'assignee', 'start_date', 'end_date', 'priority']


class GroupSerializer(serializers.ModelSerializer):
    members = UserSerializer(many=True, read_only=True)
    admin = UserSerializer(read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'group_uuid', 'name', 'icon', 'members', 'description', 'admin']
        read_only_fields = ['admin', 'group_uuid']

class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']


class AddMemberToGroupSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)



class GroupTagCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupTag
        fields = ['name', 'color']


class GroupTagSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = GroupTag
        fields = ['code', 'name', 'color', 'group']
        read_only_fields = ['id', 'group', 'code']