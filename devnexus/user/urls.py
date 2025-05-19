from django.urls import path
from user import views

app_name = "user"

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("registration/", views.RegisterView.as_view(), name="registration"),
    path("change_password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("me/", views.CurrentUserProfileView.as_view(), name="me"),
    path("<str:username>/", views.UserProfileView.as_view(), name="profile"),
    path("<str:username>/<str:group_uuid>/", views.UserProfileGroupView.as_view(), name="profile_group"),
]

