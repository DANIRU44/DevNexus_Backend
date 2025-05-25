from django.urls import path
from .views import *


app_name = 'group'

urlpatterns = [
    path('', GroupCreateView.as_view(), name='group-create'),
    path('<str:group_uuid>/', GroupDetailView.as_view(), name='group-detail'),
    path('<str:group_uuid>/add_members/', AddMemberToGroupView.as_view(), name='add_member_to_group'),

    path('<str:group_uuid>/cards/create/', CardCreateView.as_view(), name='card-create'),
    path('<str:group_uuid>/cards/all/', CardListView.as_view(), name='card-list'),
    path('<str:group_uuid>/cards/<str:code>/', CardDetailView.as_view(), name='card-detail'),

    path('<str:group_uuid>/tags/create/', GroupTagCreateView.as_view(), name='tag-create'),
    path('<str:group_uuid>/tags/all/', GroupTagListView.as_view(), name='group-tags-list'),
    path('<str:group_uuid>/tags/<str:code>/', GroupTagDetailView.as_view(), name='tag-detail'),

    path('<str:group_uuid>/usertags/create/', UserTagCreateView.as_view(), name='usertag-create'),
    path('<str:group_uuid>/usertags/delete/<str:username>/<str:tag_code>/', UserTagDeleteView.as_view(), name='usertag-delete'),

    path('<str:group_uuid>/cardtags/create/', GroupCardTagCreateView.as_view(), name='cardtag-create'),
    path('<str:group_uuid>/cardtags/all/', GroupCardTagListView.as_view(), name='group-cardtags-list'),
    path('<str:group_uuid>/cardtags/<str:code>/', GroupCardTagDetailView.as_view(), name='cardteg-detail'),

    path('<str:group_uuid>/columns/create/', ColumnBoardCreateView.as_view(), name='column-create'),
    path('<str:group_uuid>/columns/<id>/', ColumnBoardDetailView.as_view(), name='column'),
]