from typing import List
from pathlib import Path, PurePath
import uuid


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


def prep_uuid_for_qry(uuid_: str | uuid.UUID) -> str:
    # hotfix for https://stackoverflow.com/questions/46377715/sqlalchemy-query-filter-does-not-work
    # find better solution.
    if isinstance(uuid_, str):
        return uuid.UUID(uuid_).hex
    elif isinstance(uuid_, uuid.UUID):
        return uuid_.hex
    else:
        raise ValueError(f"Expected {uuid.UUID} or {str}. got: {type(uuid_)}")
