from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

class UserProfileAPITestCase(APITestCase):
    # пока что простенький тест на возврат 200 без проверки структуры
    def test_user_profiles_accessibility(self):
        usernames = ['your_username', 'daniru44', 'root4', 'pads_1866', 'daniru', 'discipline_2019']
        
        for username in usernames:
            url = reverse('user:profile', args=[username])
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK, f'Профиль {username} не доступен')
