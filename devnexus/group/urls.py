from django.urls import path
from .views import *


app_name = 'group'

urlpatterns = [
    path('', GroupCreateView.as_view(), name='group-create'),
    path('<str:group_uuid>/', GroupDetailView.as_view(), name='group-detail'),
    path('<str:group_uuid>/add_member/', AddMemberToGroupView.as_view(), name='add_member_to_group'),
    path('<str:group_uuid>/cards/create/', CardCreateView.as_view(), name='card-create'),
    path('<str:group_uuid>/cards/all/', CardListView.as_view(), name='card-list'),
    path('<str:group_uuid>/cards/<str:code>/', CardDetailView.as_view(), name='card-detail'),
]
