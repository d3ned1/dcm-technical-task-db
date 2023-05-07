import logging
import re
from enum import Enum
from pathlib import Path
from typing import List, Tuple

from django.conf import settings
from django.core.files import File
from django.core.validators import FileExtensionValidator
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)


class ExtendedEnum(Enum):
    @classmethod
    def get_as_tuple(cls) -> List[Tuple]:
        #  return str representation of value to allow for objects as values
        return [(item.name, str(item.value)) for item in cls]


def validate_python_file_extension(value):
    return FileExtensionValidator(allowed_extensions=["py"])(
        value
    )


INVALID_DIR_MESSAGE = "Invalid folder name"
INVALID_DIR_ROOT_MESSAGE = f"{INVALID_DIR_MESSAGE}: cannot use file system root"
INVALID_DIR_FULL_MESSAGE = f"{INVALID_DIR_MESSAGE}: only letters, numbers, underlines and dashes separated by single " \
                           f"slashes allowed"


def validate_directory_name(value: str) -> None:
    """
    Validate path provided is not root directory
    and contains only a-z, A-Z, 0-9, -, _, /
    """
    try:
        path = Path(value)
    except Exception:
        raise ValidationError(INVALID_DIR_FULL_MESSAGE)
    else:
        if path.is_absolute():
            raise ValidationError(INVALID_DIR_ROOT_MESSAGE)
        if not re.match("^[a-zA-Z0-9-_]+(?:/[a-zA-Z0-9-_]+)*/?$", str(path)):
            raise ValidationError(INVALID_DIR_FULL_MESSAGE)


def make_upload_directory(path: str) -> Path:
    """
    Make new directory relatively to project root
    """
    directory = Path(settings.BASE_DIR) / path
    if not directory.exists():
        directory.mkdir(parents=True)
    return directory


def save_file(file: File, full_path: str | Path) -> None:
    """
    Write a file by full path
    """
    with open(full_path, "wb+") as destination:
        for chunk in file.chunks():
            destination.write(chunk)
