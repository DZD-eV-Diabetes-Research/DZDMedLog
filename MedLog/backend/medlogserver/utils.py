from typing import (
    List,
    Literal,
    Dict,
    Union,
    Tuple,
    Annotated,
    Optional,
    TYPE_CHECKING,
    Callable,
    Any,
    Type,
)

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
from getversion.main import DetailedResults
from urllib.parse import urlparse

from sqlalchemy.types import TypeDecorator, Text, String
import json
import asyncio
import threading
import csv
import io


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


from pathlib import Path
from urllib.parse import urlparse


def prepare_sqlite_parent_path_if_needed(db_url: str) -> Path | None:
    """
    Checks if the given SQL connection URL points to a SQLite file.
    If so, creates any missing parent directories for the file path and returns the path

    Parameters:
        db_url (str): The SQL database connection URL.

    Returns:
        Path | None: Path instance if it was a SQLite file and directories were ensured/created,
              None if not a SQLite file.
    """
    parsed_db_url = urlparse(db_url)

    # SQLite URLs typically look like: sqlite:///path/to/db.sqlite3
    if "sqlite" not in parsed_db_url.scheme:
        return None
    # remove sqlite style leading "/" (see https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#connect-strings)
    db_path_clean = parsed_db_url.path[1:]
    if db_path_clean == ":memory:":
        # Skip in-memory SQLite
        return None
    full_db_path = Path(db_path_clean).resolve()
    full_db_path.parent.mkdir(exist_ok=True, parents=True)
    return full_db_path


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


def humanbytes(B):
    """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
    B = float(B)
    KB = float(1024)
    MB = float(KB**2)  # 1,048,576
    GB = float(KB**3)  # 1,073,741,824
    TB = float(KB**4)  # 1,099,511,627,776

    if B < KB:
        return "{0} {1}".format(B, "Bytes" if 0 == B > 1 else "Byte")
    elif KB <= B < MB:
        return "{0:.2f} KB".format(B / KB)
    elif MB <= B < GB:
        return "{0:.2f} MB".format(B / MB)
    elif GB <= B < TB:
        return "{0:.2f} GB".format(B / GB)
    elif TB <= B:
        return "{0:.2f} TB".format(B / TB)


def get_app_version() -> str:
    import medlogserver

    get_version_result_details: DetailedResults = (
        getversion.get_module_version.__wrapped__(medlogserver)[1]
    )
    return get_version_result_details.version_found


def set_version_file(base_dir=Path("./")) -> Path:
    import medlogserver
    from importlib import reload

    version_file_path = Path(PurePath(base_dir, "__version__.py"))
    if version_file_path.exists():
        version_file_path.unlink()
    # medlogserver = reload(medlogserver)
    content = f'__version__="{get_app_version()}"\n__version_git_branch__="{get_version_git_branch_name()}"'
    print(f"Write version file to '{version_file_path}'. Content:\n{content}\n")
    version_file_path.write_text(content)
    return version_file_path


def get_version_git_branch_name() -> str:

    from medlogserver import __version_git_branch__

    return __version_git_branch__


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


async def async_enumerate(aiterable, start=0):
    index = start
    async for item in aiterable:
        yield index, item
        index += 1


class HelperUnset:
    pass


def extract_bracket_values(
    input_string: str, count: int, default=HelperUnset
) -> Tuple[str]:
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
        if default != HelperUnset:
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


def run_async_sync(awaitable) -> Any:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop running, use asyncio.run
        return asyncio.run(awaitable)

    # Already in a running loop — must run in a thread
    result_container = {}
    done = threading.Event()

    def run():
        try:
            coro_result = asyncio.run(awaitable)
            result_container["result"] = coro_result
        except Exception as e:
            result_container["exception"] = e
        finally:
            done.set()

    thread = threading.Thread(target=run)
    thread.start()
    done.wait()

    if "exception" in result_container:
        raise result_container["exception"]
    return result_container["result"]


class SqlJsonText(TypeDecorator):
    """Stores JSON-serializable Python objects as TEXT."""

    impl = Text

    def process_bind_param(self, value: Dict | None, dialect):
        return json.dumps(value) if value is not None else "{}"

    def process_result_value(self, value: str, dialect):
        if value is None:
            return {}
        return json.loads(value)


class SqlStringListText(TypeDecorator):
    """
    SQLAlchemy TypeDecorator to store a list of strings in a TEXT column,
    using CSV serialization for safe and reversible storage.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Optional[List[str]], dialect) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("Expected a list of strings.")
        if not all(isinstance(item, str) for item in value):
            raise ValueError("All items must be strings.")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(value)
        return output.getvalue().strip("\r\n")  # remove trailing newline

    def process_result_value(self, value: Optional[str], dialect) -> List[str]:
        if not value:
            return []
        input_ = io.StringIO(value)
        reader = csv.reader(input_)
        return next(reader)
