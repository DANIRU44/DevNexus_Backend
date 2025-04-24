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
    assignee = serializers.CharField(write_only=True)
    column = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ColumnBoard.objects.all()
    )
    tags = GroupCardTagSerializer(many=True, required=False)

    class Meta:
        model = Card
        fields = ['code', 'title', 'description', 'column', 'assignee', 'start_date', 'end_date', 'tags']

    def create(self, validated_data):
        # Извлекаем данные для тегов
        tags_data = validated_data.pop('tags', [])
        column = validated_data.pop('column')
        assignee_username = validated_data.pop('assignee')
        group = self.context['group']

        # Получаем пользователя
        try:
            user = User.objects.get(username=assignee_username)
        except User.DoesNotExist:
            raise serializers.ValidationError({"assignee": "Пользователь не найден"})

        # Создаем карточку
        card = Card.objects.create(
            column=column,
            assignee=user,
            group=group,
            **validated_data
        )

        tags = []
        for tag_data in tags_data:
            tag, _ = CardTag.objects.get_or_create(
                group=group,
                **tag_data
            )
            tags.append(tag)
        
        card.tags.set(tags)

        return card
    
    def update(self, instance, validated_data):

        assignee_username = validated_data.pop('assignee', None)
        if assignee_username:
            try:
                user = User.objects.get(username=assignee_username)
                instance.assignee = user
            except User.DoesNotExist:
                raise serializers.ValidationError({"assignee": "Пользователь не найден"})

        tags_data = validated_data.pop('tags', [])
        tags = []
        for tag_data in tags_data:
            tag, _ = CardTag.objects.get_or_create(
                group=instance.group,
                **tag_data
            )
            tags.append(tag)
        instance.tags.set(tags)

        return super().update(instance, validated_data)


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