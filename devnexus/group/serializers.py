from rest_framework import serializers
from user.models import User
from user.serializers import UserProfileSerializer
from .models import Group, Card, UserTag, UserTagRelation, CardTag, ColumnBoard


class GroupCardTagSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = CardTag
        fields = ['code', 'name', 'color']
        read_only_fields = ['id', 'code']


class CardSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.context.get('group')
        if group:
            self.fields['column'].queryset = ColumnBoard.objects.filter(group=group)


    column = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ColumnBoard.objects.none(),
        required=True
    )

    assignee = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        required=False,
        allow_null=True
    )
    tags = GroupCardTagSerializer(many=True, required=False)

    class Meta:
        model = Card
        fields = ['title', 'description', 'column', 'assignee', 'tags', 'code']
        read_only_fields = ['code']

    def validate(self, data):
        group = self.context.get('group')
        if group is None:
            raise serializers.ValidationError("Group not found")
        if 'column' in data and data['column'].group != group:
            raise serializers.ValidationError("Column does not belong to this group.")
        if 'assignee' in data and data['assignee'] and not group.members.filter(id=data['assignee'].id).exists():
            raise serializers.ValidationError("Assignee must be a group member.")
        return data

    def create(self, validated_data):
        tags_data = validated_data.pop('tags', [])
        card = Card.objects.create(**validated_data)
        for tag_data in tags_data:
            tag, _ = CardTag.objects.get_or_create(group=card.group, **tag_data)
            card.tags.add(tag)
        return card

    def update(self, instance, validated_data):
        tags_data = validated_data.pop('tags', [])
        instance = super().update(instance, validated_data)
        if tags_data:
            instance.tags.clear()
            for tag_data in tags_data:
                tag, _ = CardTag.objects.get_or_create(group=instance.group, **tag_data)
                instance.tags.add(tag)
        return instance
    

# class GroupSerializer(serializers.ModelSerializer):
#     members = UserProfileSerializer(many=True, read_only=True)
#     admin = UserProfileSerializer(read_only=True)

#     class Meta:
#         model = Group
#         fields = ['id', 'group_uuid', 'name', 'icon', 'members', 'description', 'admin']
#         read_only_fields = ['admin', 'group_uuid']


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


class UserTagCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserTag
        fields = ['name', 'color']


class UserTagSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = UserTag
        fields = ['code', 'name', 'color']
        read_only_fields = ['id', 'code']


class GroupCardTagCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CardTag
        fields = ['name', 'color']


class ColumnBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnBoard
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']


class GroupSerializer(serializers.ModelSerializer):
    members = UserProfileSerializer(many=True, read_only=True)
    board = ColumnBoardSerializer(many=True, read_only=True, source='columnboard_set')

    class Meta:
        model = Group
        fields = ['name', 'description', 'group_uuid', 'members', 'board']
        read_only_fields = ['group_uuid', 'members', 'board']


class UserTagRelationSerializer(serializers.ModelSerializer):
    username = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all(),
        source='user'
    )
    tag_code = serializers.SlugRelatedField(
        slug_field='code',
        queryset=UserTag.objects.all(),
        source='tag'
    )

    class Meta:
        model = UserTagRelation
        fields = ['username', 'tag_code']

    def validate(self, data):
        group = self.context['view'].group
        if data['user'] and not group.members.filter(id=data['user'].id).exists():
            raise serializers.ValidationError("User must be a group member.")
        if data['tag'].group != group:
            raise serializers.ValidationError("Tag does not belong to this group.")
        return data