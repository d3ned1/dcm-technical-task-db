from api.models import TestFilePath, TestEnvironment, TestUploadDirectory
from api.serializers import TestFilePathSerializer, TestEnvironmentSerializer, TestUploadDirectorySerializer


def get_assets():
    available_paths = TestFilePath.objects.all().order_by('path')
    test_envs = TestEnvironment.objects.all().order_by('name')
    upload_dirs = TestUploadDirectory.objects.all().order_by('directory')
    return {
        'available_paths': TestFilePathSerializer(available_paths, many=True).data,
        'test_envs': TestEnvironmentSerializer(test_envs, many=True).data,
        'upload_dirs': TestUploadDirectorySerializer(upload_dirs, many=True).data,
    }
