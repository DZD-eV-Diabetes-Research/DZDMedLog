from typing import Optional, List, Dict, Type
from sqlalchemy.types import TypeDecorator, Text, String
import json
import io
import csv
import datetime
from medlogserver.log import get_logger

log = get_logger()


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
            raise ValueError(f"All items must be strings. Got {value}")

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


class SqlStringListAny(TypeDecorator):
    """
    SQLAlchemy TypeDecorator to store a list of any basic type (str,int,bool,float,datetime,date) in a TEXT column,
    using CSV serialization for safe and reversible storage.
    """

    impl = Text
    cache_ok = True

    type_map: Dict[Type, str] = {
        str: "str",
        int: "int",
        bool: "bool",
        float: "float",
        datetime.datetime: "datetime",
        datetime.date: "date",
    }
    reverse_type_map: Dict[str, Type] = {v: k for k, v in type_map.items()}

    def process_bind_param(self, value: Optional[List[str]], dialect) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, list):
            raise ValueError("Expected a list of strings.")

        output = io.StringIO()
        writer = csv.writer(output)
        for val in value:
            # log.debug(f"val {type(val)}: {val}")
            type_name = self.type_map[type(val)]
            if isinstance(val, datetime.datetime):
                serialized = val.isoformat()
            elif isinstance(val, datetime.date):
                serialized = val.isoformat()
            else:
                serialized = str(val)
            writer.writerow([type_name, serialized])
        return output.getvalue().strip("\r\n")  # remove trailing newline

    def process_result_value(self, value: Optional[str], dialect) -> List[str]:
        if not value:
            return []

        input_ = io.StringIO(value)
        reader = csv.reader(input_)
        result = []
        for row in reader:
            if len(row) != 2:
                raise ValueError(f"Row is malformed. {row}")
            type_name, val = row
            target_type = self.reverse_type_map.get(type_name)
            if target_type is None:
                raise ValueError(f"Unsupported type name: {type_name}")

            if target_type is datetime.datetime:
                parsed = datetime.datetime.fromisoformat(val)
            elif target_type is datetime.date:
                parsed = datetime.date.fromisoformat(val)
            elif target_type is bool:
                parsed = val.lower() in ("true", "1")
            else:
                parsed = target_type(val)
            result.append(parsed)
        return result
