from django.urls import reverse
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Group, User, ColumnBoard, Card, CardTag

class CardTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Создаем тестовые данные
        self.user = User.objects.create_user(
            username='testuser', 
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
        # Исправлено: используем admin вместо owner
        self.group = Group.objects.create(
            name='Test Group',
            admin=self.user,  # 👈 вот это поле изменили
            group_uuid='testuuid123'
        )
        # Добавляем пользователя в участники группы
        self.group.members.add(self.user)
        
        self.column = ColumnBoard.objects.create(
            name='To Do',
            color='#FFFFFF',
            group=self.group
        )
        
        self.tag1 = CardTag.objects.create(
            name='Urgent',
            color='#FF0000',
            group=self.group
        )
        
        self.tag2 = CardTag.objects.create(
            name='Bug',
            color='#0000FF',
            group=self.group
        )

    # ---------------------------
    # Тесты создания карточки
    # ---------------------------
    def test_create_card_success(self):
        url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        data = {
            'title': 'New Card',
            'description': 'Card description',
            'column': 'To Do',
            'assignee': 'testuser',
            'tags': [{'name': 'Urgent'}, {'name': 'NewTag'}]
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем создание карточки
        card = Card.objects.get(code=response.data['code'])
        self.assertEqual(card.title, 'New Card')
        self.assertEqual(card.column, self.column)
        
        # Проверяем теги (существующий и новый)
        self.assertEqual(card.tags.count(), 2)
        self.assertTrue(card.tags.filter(name='NewTag').exists())

    def test_create_card_invalid_column(self):
        url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        data = {
            'title': 'New Card',
            'column': 'InvalidColumn',
            'assignee': 'testuser'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('column', response.data)

    # ---------------------------
    # Тесты получения карточки
    # ---------------------------
    def test_retrieve_card_success(self):
        # Создаем через API, чтобы получить корректный код
        create_url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        create_data = {
            'title': 'Test Card',
            'column': 'To Do',
            'assignee': 'testuser'
        }
        create_response = self.client.post(create_url, create_data, format='json')
        
        url = reverse('group:card-detail', kwargs={
            'group_uuid': self.group.group_uuid,
            'code': create_response.data['code']
        })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Card')

    def test_retrieve_card_not_found(self):
        url = reverse('group:card-detail', kwargs={
            'group_uuid': 'invalid_uuid',
            'code': '000000'
        })
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------------------
    # Тесты обновления карточки
    # ---------------------------
    def test_update_card_success(self):
        # Создаем через API
        create_url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})        
        create_data = {
            'title': 'Original Title',
            'description': 'Original Desc',
            'column': 'To Do',
            'assignee': 'testuser'
        }
        create_response = self.client.post(create_url, create_data, format='json')
        
        url = reverse('group:card-detail', kwargs={
            'group_uuid': self.group.group_uuid,
            'code': create_response.data['code']
        })
        
        new_column = ColumnBoard.objects.create(
            name='Done',
            color='#000000',
            group=self.group
        )
        
        data = {
            'title': 'Updated Title',
            'description': 'Updated Desc',
            'column': 'Done',
            'tags': [{'name': 'Bug'}]
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        card = Card.objects.get(code=create_response.data['code'])
        self.assertEqual(card.title, 'Updated Title')
        self.assertEqual(card.column, new_column)
        self.assertEqual(card.tags.count(), 1)
        self.assertTrue(card.tags.filter(name='Bug').exists())

    def test_update_card_invalid_column(self):
        # Создаем через API
        create_url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        create_data = {
            'title': 'Test Card',
            'column': 'To Do',
            'assignee': 'testuser'
        }
        create_response = self.client.post(create_url, create_data, format='json')
        
        # Колонка из другой группы
        other_group = Group.objects.create(
            name='Other Group',
            admin=self.user,
            group_uuid='otheruuid'
        )
        ColumnBoard.objects.create(
            name='Other Column',
            color='#000000',
            group=other_group
        )
        
        url = reverse('group:card-detail', kwargs={
            'group_uuid': self.group.group_uuid,
            'code': create_response.data['code']
        })
        
        data = {'column': 'Other Column'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('column', response.data)

    # ---------------------------
    # Тесты удаления карточки
    # ---------------------------
    def test_delete_card_success(self):
        # Создаем через API
        create_url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        create_data = {
            'title': 'Delete Me',
            'column': 'To Do',
            'assignee': 'testuser'
        }
        create_response = self.client.post(create_url, create_data, format='json')
        
        url = reverse('group:card-detail', kwargs={
            'group_uuid': self.group.group_uuid,
            'code': create_response.data['code']
        })
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(code=create_response.data['code']).exists())

    def test_delete_non_existent_card(self):
        url = reverse('group:card-detail', kwargs={
            'group_uuid': self.group.group_uuid,
            'code': '999999'
        })
        
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ---------------------------
    # Проверка автогенерации кода
    # ---------------------------
    def test_code_auto_generation(self):
        url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        data = {
            'title': 'Code Test',
            'column': 'To Do',
            'assignee': 'testuser'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertIsNotNone(response.data['code'])
        self.assertEqual(len(response.data['code']), 6)
        self.assertTrue(response.data['code'].isdigit())