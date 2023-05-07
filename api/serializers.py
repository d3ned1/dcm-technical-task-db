from pathlib import Path

from django.db import transaction
from rest_framework import serializers

from api.models import TestRunRequest, TestFilePath, TestEnvironment, TestUploadDirectory
from api.utils import validate_python_file_extension, validate_directory_name, save_file
from django.conf import settings


class TestRunRequestSerializer(serializers.ModelSerializer):
    env_name = serializers.ReadOnlyField(source='env.name')

    class Meta:
        model = TestRunRequest
        fields = (
            'id',
            'requested_by',
            'env',
            'path',
            'status',
            'created_at',
            'env_name'
        )
        read_only_fields = (
            'id',
            'created_at',
            'status',
            'logs',
            'env_name'
        )


class TestRunRequestItemSerializer(serializers.ModelSerializer):
    env_name = serializers.ReadOnlyField(source='env.name')

    class Meta:
        model = TestRunRequest
        fields = (
            'id',
            'requested_by',
            'env',
            'path',
            'status',
            'created_at',
            'env_name',
            'logs'
        )


class TestFilePathSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestFilePath
        fields = ('id', 'path')


class TestFileUploadRequestSerializer(serializers.Serializer):
    test_file = serializers.FileField(validators=[validate_python_file_extension])
    upload_dir = serializers.CharField(max_length=1024, validators=[validate_directory_name])

    def create(self, validated_data) -> dict:
        """
        Extract uploaded file from corresponding field.
        Check that directory already exists.
        Save file on disk or overwrite if already exists.
        """
        test_file = validated_data["test_file"]
        upload_dir = str(Path(validated_data["upload_dir"]))

        with transaction.atomic():
            test_upload_directory, _ = TestUploadDirectory.objects.get_or_create(directory=upload_dir)
            full_path = Path(settings.BASE_DIR) / upload_dir / test_file.name
            relative_path = full_path.relative_to(settings.BASE_DIR)
            test_file_path, _ = TestFilePath.objects.get_or_create(path=relative_path)
            save_file(file=test_file, full_path=full_path)

        return {"upload_dir": test_upload_directory.directory, "test_file": str(test_file_path.path)}

    def update(self, instance, validated_data):
        raise Exception("Update method is not allowed")


class TestEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestEnvironment
        fields = ('id', 'name')


class TestUploadDirectorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TestUploadDirectory
        fields = ('id', 'directory')
