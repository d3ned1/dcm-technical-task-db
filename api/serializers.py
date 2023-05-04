from pathlib import Path

from rest_framework import serializers

from api.models import TestRunRequest, TestFilePath, TestEnvironment, TestUploadDirectory
from ionos.settings import BASE_DIR


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
    test_file = serializers.FileField()
    upload_dir = serializers.CharField(max_length=1024)

    def create(self, validated_data):
        """
        Extract uploaded file from corresponding field.
        Check that directory already exists.
        Save file on disk or overwrite if already exists.
        """
        test_file = validated_data["test_file"]
        upload_dir = validated_data["upload_dir"]
        directory = Path(BASE_DIR) / upload_dir

        if not directory.exists():
            directory.mkdir()

        with open(Path(BASE_DIR) / upload_dir / test_file.name, "wb+") as destination:
            for chunk in test_file.chunks():
                destination.write(chunk)
        return validated_data

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
