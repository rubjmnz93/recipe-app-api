"""
Views for the user API.
"""
from rest_framework import generics
from .serializers import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """"Create a new user itn the system."""
    serializer_class = UserSerializer
