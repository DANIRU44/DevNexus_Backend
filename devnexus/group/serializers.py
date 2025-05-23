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
    column = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ColumnBoard.objects.none()
    ) #лютейший костыль

    column_color = serializers.CharField(source='column.color', read_only=True)
    tags = GroupCardTagSerializer(many=True, required=False)

    class Meta:
        model = Card
        fields = [
            'code', 'title', 'description', 
            'column', 'column_color', 'assignee', 
            'start_date', 'end_date', 'tags'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        group = self.context.get('group')
        if group:
            self.fields['column'].queryset = ColumnBoard.objects.filter(group=group)

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
    username = serializers.CharField(write_only=True)
    tag_code = serializers.CharField(write_only=True)

    class Meta:
        model = UserTag
        fields = ['username', 'tag_code']

    def validate(self, attrs):
        group = self.context.get('group')
        if not group:
            raise serializers.ValidationError("Группа не указана.")

        username = attrs.get('username')
        tag_code = attrs.get('tag_code')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"username": "Такого пользователя не существует"}
            )
        
        if user not in group.members.all():
            raise serializers.ValidationError(
                "Такого пользователя нет в группе."
            )
        

        try:
            tag = GroupTag.objects.get(code=tag_code, group=group)
        except GroupTag.DoesNotExist:
            raise serializers.ValidationError(
                {"tag_code": "Тег с таким кодом не найден в группе."}
            )

        if UserTag.objects.filter(user=user, tag=tag).exists():
            raise serializers.ValidationError(
                "Связь между пользователем и тегом уже существует."
            )


        attrs['user'] = user
        attrs['tag'] = tag
        return attrs

    def create(self, validated_data):
        validated_data.pop('username', None)
        validated_data.pop('tag_code', None)
        return super().create(validated_data)


class GroupCardTagCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = CardTag
        fields = ['name', 'color']


class ColumnBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColumnBoard
        fields = ['id', 'name', 'color']
        read_only_fields = ['id']