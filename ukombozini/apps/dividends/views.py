from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Dividend
from .serializers import DividendSerializer

class DividendViewSet(viewsets.ModelViewSet):
    queryset = Dividend.objects.all()
    serializer_class = DividendSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own dividends
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Automatically set the user to the current user
        serializer.save(user=self.request.user)
