from django.urls import path
from .views import GroupCreateView, GroupDetailView, AddMemberToGroupView


app_name = 'group'

urlpatterns = [
    path('', GroupCreateView.as_view(), name='group-create'),
    path('<str:group_uuid>/', GroupDetailView.as_view(), name='group-detail'),
    path('<str:group_uuid>/add_member/', AddMemberToGroupView.as_view(), name='add_member_to_group'),
]
