from rest_framework import serializers
from user.models import User
from user.serializers import UserProfileSerializer
from .models import Group, Card, GroupTag, UserTag, CardTag, ColumnBoard


class GroupCardTagSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = CardTag
        fields = ['code', 'name', 'color']
        read_only_fields = ['id', 'code']


class CardSerializer(serializers.ModelSerializer):
    assignee = serializers.CharField()
    column = serializers.CharField(source='column.name')  # Оставляем имя колонки для группировки
    tags = GroupCardTagSerializer(many=True)

    class Meta:
        model = Card
        fields = ['title', 'description', 'column', 'assignee', 'start_date', 'end_date', 'code', 'id', 'tags']

# боже оно работает!
    def create(self, validated_data):
        assignee_username = validated_data.pop('assignee')

        try:
            user = User.objects.get(username=assignee_username)
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким именем не найден.")

        card = Card.objects.create(assignee=user, **validated_data)
        return card


class GroupSerializer(serializers.ModelSerializer):
    members = UserProfileSerializer(many=True, read_only=True)
    admin = UserProfileSerializer(read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'group_uuid', 'name', 'icon', 'members', 'description', 'admin']
        read_only_fields = ['admin', 'group_uuid']

class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name']


class GroupSerializerForProfile(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'group_uuid', 'name', 'icon']


class AddMemberToGroupSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)


class GroupTagCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = GroupTag
        fields = ['name', 'color']


class GroupTagSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = GroupTag
        fields = ['code', 'name', 'color']
        read_only_fields = ['id', 'code']


class UserTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTag
        fields = ['user', 'tag']


class GroupCardTagCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CardTag
        fields = ['name', 'color']


class ColumnBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnBoard
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']