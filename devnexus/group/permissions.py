from rest_framework import permissions


class IsGroupMember(permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):

        if request.method in permissions.SAFE_METHODS:
            return obj.members.filter(id=request.user.id).exists()
        
        return request.user == obj.admin