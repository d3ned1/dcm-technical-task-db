import re
from enum import Enum
from pathlib import Path
from typing import List, Tuple

from django.core.validators import FileExtensionValidator
from rest_framework.exceptions import ValidationError


class ExtendedEnum(Enum):
    @classmethod
    def get_as_tuple(cls) -> List[Tuple]:
        #  return str representation of value to allow for objects as values
        return [(item.name, str(item.value)) for item in cls]


def validate_python_file_extension(value):
    return FileExtensionValidator(allowed_extensions=["py"])(
        value
    )


def validate_directory_name(value: str):
    path = Path(value)
    if path.is_absolute():
        raise ValidationError(f"Cannot use file system root: {value}")
    if re.match(r'^[^\\/?%*:|"<>\.]+$', value):
        raise ValidationError(f"Inappropriate folder name: {value}")
    return True
