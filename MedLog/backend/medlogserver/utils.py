from typing import List, Literal
from pathlib import Path, PurePath
import uuid
import random
import string
import getversion


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


def prep_uuid_for_qry(uuid_: str | uuid.UUID) -> str:
    # hotfix for https://stackoverflow.com/questions/46377715/sqlalchemy-query-filter-does-not-work
    # find better solution.
    if isinstance(uuid_, str):
        return uuid.UUID(uuid_).hex
    elif isinstance(uuid_, uuid.UUID):
        return uuid_.hex
    else:
        raise ValueError(f"Expected {uuid.UUID} or {str}. got: {type(uuid_)}")


def set_version_file(base_dir=Path("./")) -> Path:
    import medlogserver
    from importlib import reload

    version_file_path = Path(PurePath(base_dir, "__version__.py"))
    if version_file_path.exists():
        print(f"Delete {version_file_path.absolute()}")
        version_file_path.unlink()
    # medlogserver = reload(medlogserver)
    content = (
        f'__version__="{getversion.get_module_version.__wrapped__(medlogserver)[0]}"'
    )
    version_file_path.write_text(content)
    return version_file_path
