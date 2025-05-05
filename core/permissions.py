from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'seller'):
            return obj.seller == request.user
        elif hasattr(obj, 'reviewer'):
            return obj.reviewer == request.user
        return False


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow sellers of a listing to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'seller'):
            return obj.seller == request.user
        elif hasattr(obj, 'listing') and hasattr(obj.listing, 'seller'):
            return obj.listing.seller == request.user

        return False
