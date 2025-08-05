from rest_framework import permissions
from group.models import Group, Card, UserTag, CardTag, ColumnBoard, UserTagRelation

class IsGroupMember(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        group_uuid = view.kwargs.get('group_uuid')
        try:
            group = Group.objects.get(group_uuid=group_uuid)
            return group.members.filter(id=request.user.id).exists()
        except Group.DoesNotExist:
            return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        if isinstance(obj, Group):
            return obj.members.filter(id=request.user.id).exists()
        elif isinstance(obj, (Card, UserTag, CardTag, ColumnBoard, UserTagRelation)):
            return obj.group.members.filter(id=request.user.id).exists()
        return False


class IsGroupAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.admin
