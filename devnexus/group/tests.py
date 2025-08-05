from rest_framework.test import APIClient
from django.test import TestCase
from django.urls import reverse
from .models import *
from user.models import User
from rest_framework import status

class GroupCreateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)

    def test_create_group_success(self):
        data = {'name': 'New Group'}
        response = self.client.post(reverse('group:group-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Group.objects.count(), 1)
        group = Group.objects.first()
        self.assertEqual(group.name, 'New Group')
        self.assertEqual(group.admin, self.user)
        self.assertIn(self.user, group.members.all())

    def test_create_group_invalid_data(self):
        data = {}  # Отсутствует 'name'
        response = self.client.post(reverse('group:group-create'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_group_unauthenticated(self):
        self.client.force_authenticate(user=None)
        data = {'name': 'New Group'}
        response = self.client.post(reverse('group:group-create'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class GroupDetailViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.group = Group.objects.create(name='Test Group', admin=self.user)
        self.group.members.add(self.user)
        self.other_user = User.objects.create_user(username='otheruser', password='testpass')

    def test_get_group_detail_as_member(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('group:group-detail', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Group')

    def test_get_group_detail_as_non_member(self):
        self.client.force_authenticate(user=self.other_user)
        url = reverse('group:group-detail', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_nonexistent_group(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('group:group-detail', kwargs={'group_uuid': 'nonexistent'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_group_as_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('group:group-detail', kwargs={'group_uuid': self.group.group_uuid})
        data = {'name': 'Updated Group'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, 'Updated Group')

    def test_update_group_as_non_admin(self):
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.group.members.add(other_user)
        self.client.force_authenticate(user=other_user)
        url = reverse('group:group-detail', kwargs={'group_uuid': self.group.group_uuid})
        data = {'name': 'Updated Group'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_group_as_admin(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('group:group-detail', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Group.objects.filter(group_uuid=self.group.group_uuid).exists())

    def test_delete_group_as_non_admin(self):
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.group.members.add(other_user)
        self.client.force_authenticate(user=other_user)
        url = reverse('group:group-detail', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class CardCreateViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.group = Group.objects.create(name='Test Group', admin=self.user)
        self.group.members.add(self.user)
        self.column = ColumnBoard.objects.create(name='Column1', color='blue', group=self.group)
        self.client.force_authenticate(user=self.user)

    def test_create_card_success(self):
        data = {'title': 'Test Card', 'column': self.column.id}
        url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Card.objects.count(), 1)
        card = Card.objects.first()
        self.assertEqual(card.title, 'Test Card')
        self.assertEqual(card.column.id, self.column.id)

    def test_create_card_invalid_data(self):
        data = {'title': 'Test Card'}  # Отсутствует 'column'
        url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_card_non_member(self):
        other_user = User.objects.create_user(username='otheruser', password='testpass')
        self.client.force_authenticate(user=other_user)
        data = {'title': 'Test Card', 'column': self.column.id}
        url = reverse('group:card-create', kwargs={'group_uuid': self.group.group_uuid})
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_card_nonexistent_group(self):
        url = reverse('group:card-create', kwargs={'group_uuid': 'nonexistent'})
        data = {'title': 'Test Card', 'column': self.column.id}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)




