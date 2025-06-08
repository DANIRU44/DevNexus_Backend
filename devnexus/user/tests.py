from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User

class RegisterViewTests(APITestCase):
    def test_register_user_success(self):
        url = reverse('user:registration')  # Добавлено пространство имен
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123!@#'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().username, 'testuser')

    def test_register_user_with_existing_username(self):
        User.objects.create_user(username='testuser', email='test@example.com', password='testpassword123')
        url = reverse('user:registration')  # Добавлено пространство имен
        data = {
            'username': 'testuser',
            'email': 'newemail@example.com',
            'password': 'newpasSword123!%'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data['error'])


    def test_register_user_with_invalid_email(self):
        url = reverse('user:registration')  # Добавлено пространство имен
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'testpaSsword123%*'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['error'])


    def test_register_user_with_short_password(self):
        url = reverse('user:registration')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data['error'])


class LoginViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword123')

    def test_login_user_success(self):
        url = reverse('user:login')  # Добавлено пространство имен
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')

    def test_login_user_invalid_credentials(self):
        url = reverse('user:login')  # Добавлено пространство имен
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_user_with_nonexistent_username(self):
        url = reverse('user:login')  # Добавлено пространство имен
        data = {
            'username': 'nonexistentuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)

    def test_login_user_without_username(self):
        url = reverse('user:login')  # Добавлено пространство имен
        data = {
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)

    def test_login_user_without_password(self):
        url = reverse('user:login')  # Добавлено пространство имен
        data = {
            'username': 'testuser'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


class CurrentUserProfileViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword123')
        self.client.force_authenticate(user=self.user)

    def test_get_current_user_profile_success(self):
        url = reverse('user:me')  # Добавлено пространство имен
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'testuser')

    def test_update_current_user_profile_success(self):
        url = reverse('user:me')  # Добавлено пространство имен
        data = {
            'username': 'newusername',
            'email': 'newemail@example.com'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newusername')
        self.assertEqual(self.user.email, 'newemail@example.com')

    def test_update_current_user_password_with_incorrect_old_password(self):
        url = reverse('user:change-password')
        data = {
            'old_password': 'wrong_password',
            'new_password': 'new_password123'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    # def test_update_current_user_password_without_old_password(self):
    #     self.client.force_authenticate(user=self.user)
    #     data = {
    #         'new_password': 'new_password123'
    #     }
    #     response = self.client.put('/api/user/change_password/', data)
    #     self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    #     self.assertIn('error', response.data)
    #     self.assertEqual(response.json()['error'], 'Для изменения пароля укажите текущий пароль')


class UserProfileViewTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password123')
        self.user2 = User.objects.create_user(username='user2', password='password123')
        self.client.force_authenticate(user=self.user1)

    def test_get_user_profile_success(self):
        url = reverse('user:profile', kwargs={'username': 'user2'})  # Добавлено пространство имен
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['username'], 'user2')

    def test_get_user_profile_nonexistent_user(self):
        response = self.client.get('/api/user/profile/nonexistent_user/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_profile_as_owner(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('user:profile', kwargs={'username': 'user2'})  # Добавлено пространство имен
        data = {
            'username': 'updatedusername',
            'email': 'updatedemail@example.com'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user2.refresh_from_db()
        self.assertEqual(self.user2.username, 'updatedusername')
        self.assertEqual(self.user2.email, 'updatedemail@example.com')

    def test_update_user_profile_as_non_owner(self):
        url = reverse('user:profile', kwargs={'username': 'user2'})  # Добавлено пространство имен
        data = {
            'username': 'hackedusername'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
