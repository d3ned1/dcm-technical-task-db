from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import TestRunRequest
from api.serializers import TestRunRequestSerializer, TestRunRequestItemSerializer, TestFileUploadRequestSerializer
from api.tasks import execute_test_run_request
from api.usecases import get_assets


class TestFileUploadRequestAPIView(APIView):
    parser_classes = [MultiPartParser]
    serializer_class = TestFileUploadRequestSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.create(serializer.validated_data)
        return Response(data, status=status.HTTP_201_CREATED)


class TestRunRequestAPIView(ListCreateAPIView):
    serializer_class = TestRunRequestSerializer
    queryset = TestRunRequest.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        instance = serializer.save()
        execute_test_run_request.delay(instance.id)


class TestRunRequestItemAPIView(RetrieveAPIView):
    serializer_class = TestRunRequestItemSerializer
    queryset = TestRunRequest.objects.all()
    lookup_field = 'pk'


class AssetsAPIView(APIView):
    @staticmethod
    def get(request):
        return Response(status=status.HTTP_200_OK, data=get_assets())
