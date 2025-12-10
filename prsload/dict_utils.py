import re
from typing import Any

array_index = re.compile(r"\[(-)?\d]")


def safe_traverse(data: dict[str, Any] | list[Any], path: str, backup_value: Any = None) -> Any:
    """Get a nested value from the dictionary.
    Suppress all Key and Value errors and return backup_value,
    if the real value cannot be found.

    Path has to have attrs separated by a dot. It supports named attrs
    and array indexes,
      example: merged_prs.[0].title

    """
    attrs = path.split(".")
    value: Any = data
    try:
        for attr in attrs:
            if value is None:
                return backup_value

            if array_index.match(attr):
                # is attr an index: [0], [-1], [120]
                num = int(attr[1:-1])
                value = value[num]
            else:
                # or a key
                value = value[attr]

    except (KeyError, ValueError, AttributeError, TypeError):
        return backup_value

    return value if value is not None else backup_value
