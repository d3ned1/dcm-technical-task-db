from django.urls import path

from .views import TestRunRequestAPIView, TestRunRequestItemAPIView, AssetsAPIView, TestFileUploadRequestAPIView

urlpatterns = [
    path('assets', AssetsAPIView.as_view(), name='assets'),
    path('test-file', TestFileUploadRequestAPIView.as_view(), name='test_file_upload_req'),
    path('test-run', TestRunRequestAPIView.as_view(), name='test_run_req'),
    path('test-run/<pk>', TestRunRequestItemAPIView.as_view(), name='test_run_req_item'),
]
