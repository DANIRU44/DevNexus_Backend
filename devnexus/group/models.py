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


class GroupTag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='tags')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} ({self.group.name})"
    

class Card(models.Model):
    """Карточки с заданиями в группах"""
    code = models.CharField(max_length=6, unique=True, editable=False)  # Уникальный шестизначный код карточки
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, max_length=700)
    status = models.CharField(max_length=50, choices=[('todo', 'Сделать'), ('in_progress', 'В процесс'), ('done', 'Готово')], default='todo')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    priority = models.IntegerField(choices=[(1, 'Низкий'), (2, 'Средний'), (3, 'Высокий')], default=2)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)

    class Meta:
        db_table = "card"
        verbose_name = "Карточка"
        verbose_name_plural = "Карточки"

    def save(self, *args, **kwargs):
        # Генерируем уникальный шестизначный код
        if not self.code:
            last_card = Card.objects.order_by('code').last()
            if last_card:
                last_code = int(last_card.code)
                new_code = last_code + 1
            else:
                new_code = 1
            
            self.code = f"{new_code:06}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.group.name} {self.title} {self.code}"