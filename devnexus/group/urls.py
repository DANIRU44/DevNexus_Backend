from django.urls import path
from .views import *


app_name = 'group'

urlpatterns = [
    path('', GroupCreateView.as_view(), name='group-create'),
    path('<str:group_uuid>/', GroupDetailView.as_view(), name='group-detail'),
    path('<str:group_uuid>/add_member/', AddMemberToGroupView.as_view(), name='add_member_to_group'),

    path('<str:group_uuid>/card/create/', CardCreateView.as_view(), name='card-create'),
    path('<str:group_uuid>/card/all/', CardListView.as_view(), name='card-list'),
    path('<str:group_uuid>/card/<str:code>/', CardDetailView.as_view(), name='card-detail'),

    path('<str:group_uuid>/tag/create/', GroupTagCreateView.as_view(), name='tag-create'),
    # path('<str:group_uuid>/tag/all', GroupTagListView.as_view(), name='group-tags-list'),
    path('<str:group_uuid>/tag/<str:code>/', GroupTagDetailView.as_view(), name='tag-detail'),

    path('<str:group_uuid>/usertag/create/', UserTagCreateView.as_view(), name='usertag-create'),
    path('<str:group_uuid>/usertag/delete/<str:username>/<str:tag>/', UserTagDeleteView.as_view(), name='usertag-delete'),

    path('<str:group_uuid>/cardtag/create/', GroupCardTagCreateView.as_view(), name='cardtag-create'),
    path('<str:group_uuid>/cardtag/all', GroupCardTagListView.as_view(), name='group-cardtags-list'),
    path('<str:group_uuid>/cardtag/<str:code>/', GroupCardTagDetailView.as_view(), name='cardteg-detail'),

    path('<str:group_uuid>/column/create/', ColumnBoardCreateView.as_view(), name='column-create'),
    path('<str:group_uuid>/column/<id>/', ColumnBoardDetailView.as_view(), name='column-create'),
]