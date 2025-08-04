# group/tests/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from group.models import Group, Card, UserTag, UserTagRelation, CardTag, ColumnBoard

User = get_user_model()

class GroupAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123!'
        )
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовую группу
        self.group = Group.objects.create(
            name='Test Group',
            admin=self.user,
            description='Test description'
        )
        self.group.members.add(self.user)
        
        # URL для работы с группой
        self.group_detail_url = reverse(
            'group:group-detail',
            kwargs={'group_uuid': self.group.group_uuid}
        )
        self.add_member_url = reverse(
            'group:add_member_to_group',
            kwargs={'group_uuid': self.group.group_uuid}
        )

    def test_create_group_success(self):
        """Успешное создание новой группы"""
        url = reverse('group:group-create')
        data = {'name': 'New Team'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 2)
        self.assertEqual(response.data['name'], 'New Team')
        self.assertEqual(response.data['admin']['username'], 'testuser')

    def test_retrieve_group_details(self):
        """Получение детальной информации о группе"""
        response = self.client.get(self.group_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Group')
        self.assertEqual(response.data['admin']['username'], 'testuser')
        self.assertEqual(len(response.data['members']), 1)
        self.assertEqual(response.data['members'][0]['username'], 'testuser')

    def test_add_member_to_group_success(self):
        """Успешное добавление участника в группу"""
        new_user = User.objects.create_user(
            username='newmember',
            password='testpass'
        )
        
        data = {'username': 'newmember'}
        response = self.client.put(self.add_member_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertIn(new_user, self.group.members.all())
        self.assertEqual(response.data['success'], 'Пользователь успешно добавлен в группу.')

    def test_add_nonexistent_member(self):
        """Попытка добавить несуществующего пользователя"""
        data = {'username': 'nonexistent'}
        response = self.client.put(self.add_member_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Пользователь не найден.')

    def test_add_existing_member(self):
        """Попытка добавить уже существующего участника"""
        existing_user = User.objects.create_user(
            username='existing',
            password='testpass'
        )
        self.group.members.add(existing_user)
        
        data = {'username': 'existing'}
        response = self.client.put(self.add_member_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Пользователь уже является участником группы.')

    def test_update_group_details(self):
        """Обновление информации о группе"""
        data = {
            'name': 'Updated Group Name',
            'description': 'Updated description'
        }
        response = self.client.put(self.group_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Updated Group Name')
        self.assertEqual(self.group.description, 'Updated description')

    def test_delete_group(self):
        """Удаление группы"""
        response = self.client.delete(self.group_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Group.objects.count(), 0)


class CardAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123!'
        )
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовую группу
        self.group = Group.objects.create(
            name='Test Group',
            admin=self.user
        )
        self.group.members.add(self.user)
        
        # Создаем колонку
        self.column = ColumnBoard.objects.create(
            name='To Do',
            color='#FFFFFF',
            group=self.group
        )
        
        # URL для работы с карточками
        self.card_create_url = reverse(
            'group:card-create',
            kwargs={'group_uuid': self.group.group_uuid}
        )

    def test_create_card_success(self):
        """Успешное создание карточки"""
        data = {
            'title': 'New Task',
            'description': 'Task description',
            'column': 'To Do',
            'assignee': 'testuser'
        }
        response = self.client.post(self.card_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 1)
        card = Card.objects.first()
        self.assertEqual(card.title, 'New Task')
        self.assertEqual(card.assignee, self.user)
        self.assertEqual(card.column, self.column)

    def test_create_card_with_tags(self):
        """Создание карточки с тегами"""
        tag1 = CardTag.objects.create(
            name='Urgent',
            color='#FF0000',
            group=self.group
        )
        
        data = {
            'title': 'Bug Fix',
            'description': 'Fix critical bug',
            'column': 'To Do',
            'assignee': 'testuser',
            'tags': [{'name': 'Urgent'}, {'name': 'New'}]
        }
        response = self.client.post(self.card_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        card = Card.objects.first()
        self.assertEqual(card.tags.count(), 2)
        self.assertTrue(card.tags.filter(name='Urgent').exists())
        self.assertTrue(card.tags.filter(name='New').exists())

    def test_retrieve_card_details(self):
        """Получение информации о карточке"""
        card = Card.objects.create(
            title='Test Card',
            description='Card description',
            column=self.column,
            assignee=self.user,
            group=self.group
        )
        
        url = reverse(
            'group:card-detail',
            kwargs={
                'group_uuid': self.group.group_uuid,
                'code': card.code
            }
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Card')
        self.assertEqual(response.data['description'], 'Card description')
        self.assertEqual(response.data['assignee'], 'testuser')

    def test_update_card(self):
        """Обновление карточки"""
        card = Card.objects.create(
            title='Old Title',
            description='Old Desc',
            column=self.column,
            assignee=self.user,
            group=self.group
        )
        
        url = reverse(
            'group:card-detail',
            kwargs={
                'group_uuid': self.group.group_uuid,
                'code': card.code
            }
        )
        data = {'title': 'Updated Title', 'description': 'Updated description'}
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        card.refresh_from_db()
        self.assertEqual(card.title, 'Updated Title')
        self.assertEqual(card.description, 'Updated description')

    def test_delete_card(self):
        """Удаление карточки"""
        card = Card.objects.create(
            title='To Delete',
            column=self.column,
            assignee=self.user,
            group=self.group
        )
        
        url = reverse(
            'group:card-detail',
            kwargs={
                'group_uuid': self.group.group_uuid,
                'code': card.code
            }
        )
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Card.objects.count(), 0)


class TagAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123!'
        )
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовую группу
        self.group = Group.objects.create(
            name='Test Group',
            admin=self.user
        )
        self.group.members.add(self.user)
        
        # URL для работы с тегами
        self.user_tag_create_url = reverse(
            'group:usertags-create',
            kwargs={'group_uuid': self.group.group_uuid}
        )
        self.tag_relation_create_url = reverse(
            'group:usertagsrelation-create',
            kwargs={'group_uuid': self.group.group_uuid}
        )

    def test_create_user_tag_success(self):
        """Успешное создание тега для пользователя"""
        data = {'name': 'Developer', 'color': '#00FF00'}
        response = self.client.post(self.user_tag_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UserTag.objects.count(), 1)
        tag = UserTag.objects.first()
        self.assertEqual(tag.name, 'Developer')
        self.assertEqual(tag.color, '#00FF00')
        self.assertEqual(len(tag.code), 6)

    def test_create_duplicate_tag(self):
        """Попытка создать дубликат тега"""
        UserTag.objects.create(
            name='Developer',
            color='#00FF00',
            group=self.group
        )
        
        data = {'name': 'Developer', 'color': '#00FF00'}
        response = self.client.post(self.user_tag_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Такой тег уже существует в этой группе.')

    def test_assign_tag_to_user_success(self):
        """Успешное назначение тега пользователю"""
        tag = UserTag.objects.create(
            name='Developer',
            color='#00FF00',
            group=self.group
        )
        user = User.objects.create_user(
            username='newuser',
            password='testpass'
        )
        self.group.members.add(user)
        
        data = {'username': 'newuser', 'tag_code': tag.code}
        response = self.client.post(self.tag_relation_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserTagRelation.objects.filter(user=user, tag=tag).exists())

    def test_assign_tag_to_non_member(self):
        """Попытка назначить тег пользователю не из группы"""
        tag = UserTag.objects.create(
            name='Developer',
            color='#00FF00',
            group=self.group
        )
        user = User.objects.create_user(
            username='outsider',
            password='testpass'
        )
        # Пользователь не добавлен в группу
        
        data = {'username': 'outsider', 'tag_code': tag.code}
        response = self.client.post(self.tag_relation_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Такого пользователя нет в группе', response.data['error'])

    def test_retrieve_tag_list(self):
        """Получение списка тегов группы"""
        UserTag.objects.create(
            name='Developer',
            color='#00FF00',
            group=self.group
        )
        UserTag.objects.create(
            name='Designer',
            color='#0000FF',
            group=self.group
        )
        
        url = reverse(
            'group:user-tags-list',
            kwargs={'group_uuid': self.group.group_uuid}
        )
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Developer')
        self.assertEqual(response.data[1]['name'], 'Designer')


class ColumnAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123!'
        )
        self.client.force_authenticate(user=self.user)
        
        # Создаем тестовую группу
        self.group = Group.objects.create(
            name='Test Group',
            admin=self.user
        )
        self.group.members.add(self.user)
        
        # Создаем колонку
        self.column = ColumnBoard.objects.create(
            name='To Do',
            color='#FFFFFF',
            group=self.group
        )
        
        # URL для работы с колонками
        self.column_create_url = reverse(
            'group:column-create',
            kwargs={'group_uuid': self.group.group_uuid}
        )
        self.column_detail_url = reverse(
            'group:column',
            kwargs={'group_uuid': self.group.group_uuid, 'id': self.column.id}
        )

    def test_create_column_success(self):
        """Успешное создание колонки"""
        data = {'name': 'In Progress', 'color': '#CCCCCC'}
        response = self.client.post(self.column_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ColumnBoard.objects.count(), 2)
        self.assertEqual(response.data['name'], 'In Progress')
        self.assertEqual(response.data['color'], '#CCCCCC')

    def test_create_duplicate_column(self):
        """Попытка создать дубликат колонки"""
        data = {'name': 'To Do', 'color': '#FFFFFF'}
        response = self.client.post(self.column_create_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Такая колонка уже существует в этой группе.')

    def test_retrieve_column_details(self):
        """Получение информации о колонке"""
        response = self.client.get(self.column_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'To Do')
        self.assertEqual(response.data['color'], '#FFFFFF')

    def test_update_column(self):
        """Обновление колонки"""
        data = {'name': 'Done', 'color': '#00FF00'}
        response = self.client.put(self.column_detail_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.column.refresh_from_db()
        self.assertEqual(self.column.name, 'Done')
        self.assertEqual(self.column.color, '#00FF00')

    def test_delete_column(self):
        """Удаление колонки"""
        response = self.client.delete(self.column_detail_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ColumnBoard.objects.count(), 0)