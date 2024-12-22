from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Group

class GroupAPITestCase(APITestCase):
    
    def setUp(self):
        self.group1 = Group.objects.create(group_uuid='9n2oQ6TdPV3JxmLjPFBHGv', name='Test Group 1')
        self.group2 = Group.objects.create(group_uuid='E3LJ3H5UzTQ3WfNbuvvNGJ', name='Test Group 2')

    def test_group_accessibility(self):
        group_ids = [self.group1.group_uuid, self.group2.group_uuid]
        
        for group_id in group_ids:
            url = reverse('group:group-detail', args=[group_id])
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, f'Группа с кодом {group_id} не доступна')

            url_cards = reverse('group:card-list', args=[group_id])
            response_cards = self.client.get(url_cards)
            self.assertEqual(response_cards.status_code, status.HTTP_200_OK, f'Карточки из группы с кодом  {group_id} не доступны')
