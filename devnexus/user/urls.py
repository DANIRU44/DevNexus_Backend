from django.urls import path
from user import views

app_name = "user"

urlpatterns = [
#     path("login/", , name="login"),
    path("registration/", views.RegisterView.as_view(), name="registration"),
    # path("profile/<str:username>/", views.profile, name="profile"),
]
