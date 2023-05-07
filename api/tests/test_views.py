import io
import string
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from api.models import TestRunRequest, TestEnvironment, TestFilePath
from api.utils import INVALID_DIR_FULL_MESSAGE, INVALID_DIR_ROOT_MESSAGE


class TestTestRunRequestAPIView(TestCase):

    def setUp(self) -> None:
        self.env = TestEnvironment.objects.create(name='my_env')
        self.path1 = TestFilePath.objects.create(path='path1')
        self.path2 = TestFilePath.objects.create(path='path2')
        self.url = reverse('test_run_req')

    def test_get_empty(self):
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response_data = response.json()
        self.assertEqual([], response_data)

    def test_get_with_data(self):
        for _ in range(10):
            TestRunRequest.objects.create(requested_by='Ramadan', env=self.env)
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response_data = response.json()
        self.assertEqual(10, len(response_data))

    def test_post_no_data(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        response_data = response.json()
        self.assertEqual(
            {
                'env': ['This field is required.'],
                'path': ['This list may not be empty.'],
                'requested_by': ['This field is required.']
            },
            response_data
        )

    def test_post_invalid_path_and_env_id(self):
        response = self.client.post(self.url, data={'env': 'rambo', 'path': 'waw', 'requested_by': 'iron man'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        response_data = response.json()
        self.assertEqual({
            'env': ['Incorrect type. Expected pk value, received str.'],
            'path': ['Incorrect type. Expected pk value, received str.']
        }, response_data)

    def test_post_wrong_path_and_env_id(self):
        response = self.client.post(self.url, data={'env': 500, 'path': 500, 'requested_by': 'iron man'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        response_data = response.json()
        self.assertEqual({
            'env': ['Invalid pk "500" - object does not exist.'],
            'path': ['Invalid pk "500" - object does not exist.']
        }, response_data)

    @patch('api.views.execute_test_run_request.delay')
    def test_post_valid_multiple_paths(self, task):
        response = self.client.post(
            self.url,
            data={'env': self.env.id, 'path': [self.path1.id, self.path2.id], 'requested_by': 'iron man'}
        )
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response_data = response.json()
        self.__assert_valid_response(response_data, [self.path1.id, self.path2.id])
        self.assertTrue(task.called)
        task.assert_called_with(response_data['id'])

    @patch('api.views.execute_test_run_request.delay')
    def test_post_valid_one_path(self, task):
        response = self.client.post(self.url,
                                    data={'env': self.env.id, 'path': self.path1.id, 'requested_by': 'iron man'})
        self.assertEqual(status.HTTP_201_CREATED, response.status_code)
        response_data = response.json()
        self.__assert_valid_response(response_data, [self.path1.id])
        self.assertTrue(task.called)
        task.assert_called_with(response_data['id'])

    def __assert_valid_response(self, response_data, expected_paths):
        self.assertIn('created_at', response_data)
        self.assertIn('env', response_data)
        self.assertIn('env_name', response_data)
        self.assertIn('id', response_data)
        self.assertIn('path', response_data)
        self.assertIn('requested_by', response_data)
        self.assertIn('status', response_data)

        self.assertIsNotNone(response_data['created_at'])
        self.assertEqual(self.env.id, response_data['env'])
        self.assertEqual(self.env.name, response_data['env_name'])
        self.assertEqual(expected_paths, response_data['path'])
        self.assertEqual('iron man', response_data['requested_by'])
        self.assertEqual(TestRunRequest.StatusChoices.CREATED.name, response_data['status'])

        self.assertEqual(1, TestRunRequest.objects.filter(requested_by='iron man', env_id=self.env.id).count())


class TestRunRequestItemAPIView(TestCase):

    def setUp(self) -> None:
        self.env = TestEnvironment.objects.create(name='my_env')
        self.test_run_req = TestRunRequest.objects.create(
            requested_by='Ramadan',
            env=self.env
        )
        self.path1 = TestFilePath.objects.create(path='path1')
        self.path2 = TestFilePath.objects.create(path='path2')
        self.test_run_req.path.add(self.path1)
        self.test_run_req.path.add(self.path2)
        self.url = reverse('test_run_req_item', args=(self.test_run_req.id,))

    def test_get_invalid_pk(self):
        self.url = reverse('test_run_req_item', args=(8897,))
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)

    def test_get_valid(self):
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        response_data = response.json()
        self.assertIn('created_at', response_data)
        self.assertIn('env', response_data)
        self.assertIn('env_name', response_data)
        self.assertIn('id', response_data)
        self.assertIn('logs', response_data)
        self.assertIn('path', response_data)
        self.assertIn('requested_by', response_data)
        self.assertIn('status', response_data)

        self.assertIsNotNone(response_data['created_at'])
        self.assertEqual(self.env.id, response_data['env'])
        self.assertEqual(self.env.name, response_data['env_name'])
        self.assertEqual(self.test_run_req.id, response_data['id'])
        self.assertEqual(self.test_run_req.logs, response_data['logs'])
        self.assertEqual([self.path1.id, self.path2.id], response_data['path'])
        self.assertEqual(self.test_run_req.requested_by, response_data['requested_by'])
        self.assertEqual(self.test_run_req.status, response_data['status'])


class TestAssetsAPIView(TestCase):

    def setUp(self) -> None:
        self.url = reverse('assets')

    @patch('api.views.get_assets', return_value={'k': 'v'})
    def test_get(self, _):
        response = self.client.get(self.url)
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({'k': 'v'}, response.json())


class TestFileUploadRequestAPIView(TestCase):
    def setUp(self) -> None:
        self.url = reverse('test_file_upload_req')
        self.correct_ext_file = io.BytesIO(b"PYa\x01\x00\x01\x00\x00\x00\x00")
        self.correct_ext_file.name = "test_suite.py"
        self.incorrect_ext_file = io.BytesIO(b"PYa\x01\x00\x01\x00\x00\x00\x00")
        self.incorrect_ext_file.name = "test_suite.go"

    def test_post_no_data(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        response_data = response.json()
        self.assertEqual(
            {'test_file': ['No file was submitted.'], 'upload_dir': ['This field is required.']},
            response_data
        )

    def test_post_not_a_file(self):
        response = self.client.post(self.url, data={'test_file': 'string', 'upload_dir': 'test_dir'})
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        response_data = response.json()
        self.assertEqual(
            {'test_file': ['The submitted data was not a file. Check the encoding type on the form.']},
            response_data
        )

    @patch('api.models.make_upload_directory', return_value=Path(settings.BASE_DIR) / "test_dir")
    @patch('api.serializers.save_file')
    def test_post_file(self, *_):
        with self.subTest('Correct extension'):
            response = self.client.post(
                self.url, data={'test_file': self.correct_ext_file, 'upload_dir': 'test_dir'}
            )
            self.assertEqual(status.HTTP_201_CREATED, response.status_code)
            self.assertEqual(response.json(), {
                'test_file': "test_dir/" + self.correct_ext_file.name,
                'upload_dir': 'test_dir'
            })

        with self.subTest('Incorrect extension'):
            response = self.client.post(
                self.url, data={'test_file': self.incorrect_ext_file, 'upload_dir': 'test_dir'}
            )
            self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
            self.assertEqual(response.json(), {
                'test_file': ['File extension “go” is not allowed. Allowed extensions are: py.']
            })

    @patch('api.serializers.save_file')
    def test_post_directory(self, _):
        """
        processed_by_pathlib symbols are correctly processed by Path
        """
        string_digits_letters = string.digits + string.ascii_letters + '_-'
        processed_by_pathlib = {'\t', '\n', '\x0b', '\x0c', '\r', ' ', '.', '/'}
        not_allowed = set(string_digits_letters) ^ set(string.printable) ^ processed_by_pathlib
        valid_directories = ["dir1/", "dir2", "dir2//", "dir2/.", "dir_3/dir-4/"]
        root_directories = ["/dir1/", "/dir2", "/dir_3/dir-4/"]
        invalid_directories = ["dir_3!/dir-4/", "!", "dir/dir.py"] + [
            "dir/" + chr(c) for c in range(128) if chr(c) in not_allowed
        ]

        for directory in valid_directories:
            with patch('api.models.make_upload_directory', return_value=Path(settings.BASE_DIR) / directory):
                with self.subTest(f"checking valid directory: {directory}"):
                    self.correct_ext_file = io.BytesIO(b"PYa\x01\x00\x01\x00\x00\x00\x00")
                    self.correct_ext_file.name = "test_suite.py"
                    response = self.client.post(
                        self.url, data={'test_file': self.correct_ext_file, 'upload_dir': directory}
                    )
                    directory_path = Path(directory)
                    file_path = directory_path.joinpath(self.correct_ext_file.name)
                    self.assertEqual(response.json(), {
                        'test_file': str(file_path), "upload_dir": str(directory_path)
                    })
                    self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        # noinspection DuplicatedCode
        for root_directory in root_directories:
            with patch('api.models.make_upload_directory', return_value=Path(settings.BASE_DIR) / root_directory):
                with self.subTest(f"checking root directory: {root_directory}"):
                    self.correct_ext_file = io.BytesIO(b"PYa\x01\x00\x01\x00\x00\x00\x00")
                    self.correct_ext_file.name = "test_suite.py"
                    response = self.client.post(
                        self.url, data={'test_file': self.correct_ext_file, 'upload_dir': root_directory}
                    )
                    self.assertEqual(response.json(), {"upload_dir": [INVALID_DIR_ROOT_MESSAGE]})
                    self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        # noinspection DuplicatedCode
        for invalid_directory in invalid_directories:
            with patch('api.models.make_upload_directory', return_value=Path(settings.BASE_DIR) / invalid_directory):
                with self.subTest(f"checking invalid directory: {invalid_directory}"):
                    self.correct_ext_file = io.BytesIO(b"PYa\x01\x00\x01\x00\x00\x00\x00")
                    self.correct_ext_file.name = "test_suite.py"
                    response = self.client.post(
                        self.url, data={'test_file': self.correct_ext_file, 'upload_dir': invalid_directory}
                    )
                    self.assertEqual(response.json(), {"upload_dir": [INVALID_DIR_FULL_MESSAGE]})
                    self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

        for blank in ['', 'dir/\x00']:
            with self.subTest(f"checking blank directory"):
                with patch('api.models.make_upload_directory', return_value=Path(settings.BASE_DIR) / blank):
                    self.correct_ext_file = io.BytesIO(b"PYa\x01\x00\x01\x00\x00\x00\x00")
                    self.correct_ext_file.name = "test_suite.py"
                    response = self.client.post(
                        self.url, data={'test_file': self.correct_ext_file, 'upload_dir': ""}
                    )
                    self.assertEqual(response.json(), {"upload_dir": ['This field may not be blank.']})
                    self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
