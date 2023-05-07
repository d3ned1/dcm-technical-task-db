import io
import string
from pathlib import Path
from unittest.mock import patch, mock_open

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.test import SimpleTestCase
from rest_framework import exceptions

from api.models import TestRunRequest
from api.utils import validate_python_file_extension, make_upload_directory, validate_directory_name, save_file, \
    INVALID_DIR_ROOT_MESSAGE, INVALID_DIR_FULL_MESSAGE


class TestExtendedEnum(SimpleTestCase):
    def test_get_as_tuple(self):
        self.assertEqual(
            [
                ('SUCCESS', 'SUCCESS'),
                ('RUNNING', 'RUNNING'),
                ('FAILED', 'FAILED'),
                ('CREATED', 'CREATED'),
                ('RETRYING', 'RETRYING'),
                ('FAILED_TO_START', 'FAILED_TO_START')
            ],
            TestRunRequest.StatusChoices.get_as_tuple()
        )


class TestValidatePythonFileExtension(SimpleTestCase):
    def test_validate_python_file_extension(self):
        valid_path = Path("test.py")
        invalid_path = Path("test.go")
        self.assertEqual(validate_python_file_extension(valid_path), None)
        with self.assertRaises(ValidationError):
            validate_python_file_extension(invalid_path)


class TestValidateDirectoryName(SimpleTestCase):
    def setUp(self) -> None:
        self.string_digits_letters = string.digits + string.ascii_letters + '_-'
        self.processed_by_pathlib = {'\t', '\n', '\x0b', '\x0c', '\r', ' ', '.', '/'}
        self.not_allowed = set(self.string_digits_letters) ^ set(string.printable) ^ self.processed_by_pathlib

        self.valid_directories = ["dir1/", "dir2", "dir2//", "dir2/.", "dir_3/dir-4/"]
        self.root_directories = ["/dir1/", "/dir2", "/dir_3/dir-4/"]
        self.invalid_directories = ["dir_3!/dir-4/", "!", "dir/dir.py"] + [
            "dir/" + chr(c) for c in range(128) if chr(c) in self.not_allowed
        ]

    def test_invalid(self):
        for invalid_directory in self.invalid_directories:
            with self.assertRaises(exceptions.ValidationError, msg=INVALID_DIR_FULL_MESSAGE):
                validate_directory_name(invalid_directory)

    def test_root(self):
        for root_directory in self.root_directories:
            with self.assertRaises(exceptions.ValidationError, msg=INVALID_DIR_ROOT_MESSAGE):
                validate_directory_name(root_directory)

    def test_valid(self):
        for valid_directory in self.valid_directories:
            self.assertEqual(validate_directory_name(valid_directory), None)


class TestMakeDirectory(SimpleTestCase):
    def setUp(self) -> None:
        self.path = "test_dir_created"

    @patch('api.utils.Path.exists')
    @patch('api.utils.Path.mkdir')
    def test_create_directory_if_not_exists(self, mock_mkdir, mock_exists):
        mock_exists.return_value = False
        self.assertEqual(make_upload_directory(self.path), Path(settings.BASE_DIR) / self.path)
        mock_mkdir.assert_called_once()
        mock_exists.assert_called_once()
        mock_mkdir.assert_called_with(parents=True)

    @patch('api.utils.Path.exists')
    @patch('api.utils.Path.mkdir')
    def test_create_directory_if_exists(self, mock_mkdir, mock_exists):
        mock_exists.return_value = True
        self.assertEqual(make_upload_directory(self.path), Path(settings.BASE_DIR) / self.path)
        mock_mkdir.assert_not_called()
        mock_exists.assert_called_once()


class TestSaveFile(SimpleTestCase):
    def test_save_file(self):
        file = File(io.BytesIO(b"123"), 'test_file.py')
        full_path = 'test_file.py'

        open_mock = mock_open()
        with patch("api.utils.open", open_mock, create=True):
            save_file(file, full_path)

        open_mock.assert_called_with(full_path, "wb+")
        open_mock.return_value.write.assert_called_once_with(b'123')
