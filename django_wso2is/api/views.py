from rest_framework import generics, permissions
from rest_framework.response import Response

from .serializers import GetTokenSerializer, RefreshTokenSerializer


class BaseTokenAPIView(generics.GenericAPIView):
    serializer_class = None
    # Allow anonymous users
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetTokenAPIView(BaseTokenAPIView):
    serializer_class = GetTokenSerializer


class RefreshTokenAPIView(BaseTokenAPIView):
    serializer_class = RefreshTokenSerializer
