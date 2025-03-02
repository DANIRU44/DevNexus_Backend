from django.db import models
from user.models import User
import shortuuid

class Group(models.Model):
    name = models.CharField(max_length=30)
    group_uuid = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    admin = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    icon = models.ImageField(upload_to='group_icons/', blank=True)
    members = models.ManyToManyField(User, related_name='group_memberships')
    description = models.TextField(max_length=200, blank=True)


    class Meta:
        db_table = "group"
        verbose_name = "Группы"
        verbose_name_plural = "Группы"


    def __str__(self):
        return self.name


# решил разделить одну модель с тегами на две, так-как это позволит присваивать существующие теги, а не прописывать их каждый раз 
class GroupTag(models.Model):
    code = models.CharField(max_length=6, unique=True, editable=False)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    group = models.ForeignKey(Group, to_field='group_uuid', on_delete=models.CASCADE, related_name='available_tags')

    class Meta:
        unique_together = ('name', 'color', 'group')

    def save(self, *args, **kwargs):
        # Генерируем уникальный шестизначный код
        if not self.code:
            last_card = GroupTag.objects.filter(group=self.group).order_by('code').last()
            if last_card:
                last_code = int(last_card.code)
                new_code = last_code + 1
            else:
                new_code = 1
            
            self.code = f"{new_code:06}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.group.name})"


class UserTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tag = models.ForeignKey(GroupTag, to_field='code', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'tag')

    def __str__(self):
        return f"{self.user.username} - {self.tag.name}"
    

class CardTag(models.Model):
    code = models.CharField(max_length=6, unique=True, editable=False)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    group = models.ForeignKey(Group, to_field='group_uuid', on_delete=models.CASCADE, related_name='available_card_tags')

    class Meta:
        unique_together = ('name', 'color', 'group')

    def save(self, *args, **kwargs):
        # Генерируем уникальный шестизначный код
        if not self.code:
            last_card = CardTag.objects.filter(group=self.group).order_by('code').last()
            if last_card:
                last_code = int(last_card.code)
                new_code = last_code + 1
            else:
                new_code = 1
            
            self.code = f"{new_code:06}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.group.name})"


class ColumnBoard(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    group = models.ForeignKey(Group, to_field='group_uuid', on_delete=models.CASCADE, related_name='columns')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'group'], name='unique_column_name_per_group')
        ]

    def __str__(self):
        return f"{self.name} - {self.group.name}"



class Card(models.Model):
    """Карточки с заданиями в группах"""
    code = models.CharField(max_length=6, unique=True, editable=False)  # Уникальный шестизначный код карточки
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, max_length=700)
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    tags = models.ManyToManyField(CardTag, related_name='card_tags')
    column = models.ForeignKey(ColumnBoard, on_delete=models.CASCADE, related_name='cards')

    class Meta:
        db_table = "card"
        verbose_name = "Карточка"
        verbose_name_plural = "Карточки"

    def save(self, *args, **kwargs):
        # Генерируем уникальный шестизначный код
        if not self.code:
            last_card = Card.objects.filter(group=self.group).order_by('code').last()
            if last_card:
                last_code = int(last_card.code)
                new_code = last_code + 1
            else:
                new_code = 1
            
            self.code = f"{new_code:06}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.group.name} {self.title} {self.code}"