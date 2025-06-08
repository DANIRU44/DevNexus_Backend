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

    path('<str:group_uuid>/usertags/create/', UserTagCreateView.as_view(), name='usertags-create'),
    path('<str:group_uuid>/usertags/all/', UserTagListView.as_view(), name='user-tags-list'),
    path('<str:group_uuid>/usertags/<str:code>/', UserTagDetailView.as_view(), name='usertags-detail'),

    path('<str:group_uuid>/usertagsrelation/create/', UserTagRelationCreateView.as_view(), name='usertagsrelation-create'),
    path('<str:group_uuid>/usertagsrelation/delete/<str:username>/<str:tag_code>/', UserTagRelationCreateView.as_view(), name='usertagsrelation-delete'),

    path('<str:group_uuid>/cardtags/create/', GroupCardTagCreateView.as_view(), name='cardtag-create'),
    path('<str:group_uuid>/cardtags/all/', GroupCardTagListView.as_view(), name='group-cardtags-list'),
    path('<str:group_uuid>/cardtags/<str:code>/', GroupCardTagDetailView.as_view(), name='cardteg-detail'),

    path('<str:group_uuid>/columns/create/', ColumnBoardCreateView.as_view(), name='column-create'),
    path('<str:group_uuid>/columns/<id>/', ColumnBoardDetailView.as_view(), name='column'),
]