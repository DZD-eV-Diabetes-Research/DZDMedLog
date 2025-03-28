from typing import List, Literal, Dict, Union, Tuple, Annotated, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from hashlib import _Hash as Hash  # https://github.com/python/typeshed/issues/2928
import hashlib
from pathlib import Path, PurePath
import uuid
import random
import re
import string
import getversion
import json
import fastapi
import pydantic
import os


def to_path(
    *args: str | Path | PurePath | List[str | Path | PurePath],
    absolute: bool = True,
    expanduser: bool = True,
) -> Path:
    """Combine path fragments into one pathlib.Path

    Args:
        * (str, Path, PurePath): Provide multiple path fragment in any reasonable format that will be combined in one Path
        absolute (bool, optional): _description_. Defaults to True.
        expanduser (bool, optional): _description_. Defaults to True.

    Returns:
        Path: _description_
    """
    result_path_fragments: List[Path] = []
    for arg in args:
        if isinstance(arg, str):
            result_path_fragments.append(Path(arg))
        elif isinstance(arg, PurePath):
            result_path_fragments.append(arg)
        elif isinstance(arg, PurePath):
            result_path_fragments.append(Path(arg))
        elif isinstance(arg, list):
            for sub_arg in arg:
                result_path_fragments.append(
                    to_path(sub_arg, expanduser=False, absolute=False)
                )
    result_path = Path.joinpath(*result_path_fragments)
    if expanduser:
        result_path = result_path.expanduser()
    if absolute:
        result_path = result_path.absolute()
    return result_path


def get_random_string(
    length: int = 32,
    allowed_char_sets: List[str] = [string.ascii_lowercase, string.digits],
) -> str:
    letters = "".join(allowed_char_sets)
    return "".join(random.choice(letters) for i in range(length))


def val_means_true(s: int | str | bool) -> bool:
    if isinstance(s, bool):
        return s
    if isinstance(s, int) and s == 1:
        return True
    if s.lower() in ["true", "yes", "y", "1"]:
        return True
    return False


def set_version_file(base_dir=Path("./")) -> Path:
    import medlogserver
    from importlib import reload

    version_file_path = Path(PurePath(base_dir, "__version__.py"))
    if version_file_path.exists():
        version_file_path.unlink()
    # medlogserver = reload(medlogserver)
    content = (
        f'__version__="{getversion.get_module_version.__wrapped__(medlogserver)[0]}"'
    )
    version_file_path.write_text(content)
    return version_file_path


def sanitize_string(s: str, replace_space_with: str = "_") -> str:
    return "".join(
        char.lower() if char.isalpha() else "_" if char == " " else char
        for char in s
        if char.isalnum() or char == " "
    )


class JSONEncoderMedLogCustom(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            # if the obj is uuid, we simply return the value of uuid
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def http_exception_to_resp_desc(e: fastapi.HTTPException) -> Dict[int, str]:
    """Translate a fastapi.HTTPException into fastapi OpenAPI response description to be used as a additional response
    https://fastapi.tiangolo.com/advanced/additional-responses/
    """
    return {
        e.status_code: {
            "description": e.detail,
            "model": pydantic.create_model("Error", detail=(Dict[str, str], e.detail)),
        },
    }


def path_is_parent(parent_path: Path | str, child_path: Path | str) -> bool:
    # check if a path is a subpath of another.
    # e.g. "/tmp/parent" is parent of "/tmp/paren/child/file.txt"
    # kudos to: https://stackoverflow.com/a/37095733/12438690
    # Smooth out relative path names, note: if you are concerned about symbolic links, you should use os.path.realpath too
    parent_path = os.path.abspath(parent_path)
    child_path = os.path.abspath(child_path)

    # Compare the common path of the parent and child path with the common path of just the parent path. Using the commonpath method on just the parent path will regularise the path name in the same way as the comparison that deals with both paths, removing any trailing path separator
    return os.path.commonpath([parent_path]) == os.path.commonpath(
        [parent_path, child_path]
    )


class Unset:
    pass


def extract_bracket_values(input_string: str, count: int, default=Unset) -> Tuple[str]:
    """
    Extracts a specified number of values enclosed in square brackets from a given string.

    This function searches for values within square brackets (`[...]`) in the input string and
    returns a tuple containing the specified number of extracted values. If there are fewer values
    found than the requested count, the function will either fill the remaining positions with a
    provided default value or raise a `ValueError` if no default is given.

    Parameters:
    ----------
    input_string : str
        The string from which to extract values enclosed in square brackets.
    count : int
        The number of bracketed values to extract. If fewer values are found than this count and
        no default value is provided, a `ValueError` is raised.
    default_value : any, optional
        The value to use for missing entries if the string contains fewer than the required count.
        If `None` (default), an exception is raised if the count cannot be met.

    Returns:
    -------
    tuple
        A tuple containing exactly `count` values, with missing values filled by `default_value`
        if specified.

    Raises:
    ------
    ValueError
        If `count` values cannot be found and `default_value` is not provided.

    Examples:
    --------
    >>> extract_bracket_values("PACKAGE.CSV[ID]>[PRODUCTID]", 2)
    ('ID', 'PRODUCTID')

    >>> extract_bracket_values("PACKAGE.CSV[ID]", 2, default_value=None)
    ('ID', None)

    >>> extract_bracket_values("PACKAGE.CSV[ID]", 3, default_value="UNKNOWN")
    ('ID', 'UNKNOWN', 'UNKNOWN')

    >>> extract_bracket_values("PACKAGE.CSV[ID]", 3)
    ValueError: Expected 3 values, but only found 1.
    """
    # Find all occurrences of values inside square brackets
    matches = re.findall(r"\[([^\]]+)\]", input_string)

    # Check if we have enough matches
    if len(matches) < count:
        if default != Unset:
            # If not enough matches, extend with default value
            matches.extend([default] * (count - len(matches)))
        else:
            # Raise an error if there are not enough matches and no default value
            raise ValueError(f"Expected {count} values, but only found {len(matches)}.")

    # Return the first `count` values as a tuple
    return tuple(matches[:count])


class PathContentHasher:
    @classmethod
    def _md5_update_from_file(cls, filename: Union[str, Path], hash: "Hash") -> "Hash":
        assert Path(filename).is_file()
        file_size = os.path.getsize(filename)
        with open(str(filename), "rb") as f:
            if file_size < 10 * 1024 * 1024:  # 10MB threshold
                # Read the entire file at once
                hash.update(f.read())
            else:
                # Use larger chunks (1MB) for better performance
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    hash.update(chunk)
        return hash

    @classmethod
    def md5_file(cls, filename: Union[str, Path]) -> str:
        return str(cls._md5_update_from_file(filename, hashlib.md5()).hexdigest())

    @classmethod
    def _md5_update_from_dir(cls, directory: Union[str, Path], hash: "Hash") -> "Hash":
        assert Path(directory).is_dir(), f"{directory} not a directory"
        for path in sorted(Path(directory).iterdir(), key=lambda p: str(p).lower()):
            hash.update(path.name.encode())
            if path.is_file():
                hash = cls._md5_update_from_file(path, hash)
            elif path.is_dir():
                hash = cls._md5_update_from_dir(path, hash)
        return hash

    @classmethod
    def md5_dir(cls, directory: Union[str, Path]) -> str:
        return str(cls._md5_update_from_dir(directory, hashlib.md5()).hexdigest())
