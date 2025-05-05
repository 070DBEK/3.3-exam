from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Max, Count
from django.contrib.auth.models import User
from .models import Message
from .serializers import MessageSerializer
from listings.models import Listing


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(Q(sender=user) | Q(receiver=user))

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        user = request.user
        conversation_users = User.objects.filter(
            Q(sent_messages__receiver=user) | Q(received_messages__sender=user)
        ).distinct()
        conversations = []
        for other_user in conversation_users:
            last_message = Message.objects.filter(
                (Q(sender=user) & Q(receiver=other_user)) |
                (Q(sender=other_user) & Q(receiver=user))
            ).order_by('-created_at').first()
            unread_count = Message.objects.filter(
                sender=other_user, receiver=user, is_read=False
            ).count()

            if last_message:
                conversations.append({
                    'user': {
                        'id': other_user.id,
                        'username': other_user.username,
                        'first_name': other_user.first_name,
                        'last_name': other_user.last_name,
                        'avatar': other_user.profile.avatar.url if hasattr(other_user,
                                                                           'profile') and other_user.profile.avatar else None
                    },
                    'last_message': {
                        'id': last_message.id,
                        'content': last_message.content,
                        'is_read': last_message.is_read,
                        'created_at': last_message.created_at
                    },
                    'unread_count': unread_count,
                    'listing': {
                        'id': last_message.listing.id,
                        'title': last_message.listing.title
                    } if last_message.listing else None
                })
        return Response(conversations)

    @action(detail=False, methods=['get'], url_path='conversations/(?P<user_id>[^/.]+)')
    def conversation_with_user(self, request, user_id=None):
        user = request.user
        try:
            other_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        messages = Message.objects.filter(
            (Q(sender=user) & Q(receiver=other_user)) |
            (Q(sender=other_user) & Q(receiver=user))
        ).order_by('created_at')
        unread_messages = messages.filter(receiver=user, is_read=False)
        unread_messages.update(is_read=True)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='listings/(?P<listing_id>[^/.]+)')
    def messages_for_listing(self, request, listing_id=None):
        user = request.user
        try:
            listing = Listing.objects.get(pk=listing_id)
        except Listing.DoesNotExist:
            return Response(
                {"detail": "Listing not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        if listing.seller != user:
            return Response(
                {"detail": "You do not have permission to view these messages."},
                status=status.HTTP_403_FORBIDDEN
            )

        messages = Message.objects.filter(listing=listing)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
