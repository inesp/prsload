from os.path import abspath, dirname

from prsload.dict_utils import safe_traverse

SOURCE_DIR = dirname(dirname(dirname(abspath(__file__))))

THasMorePages = bool
TAfterCursor = str | None


def _get_abs_path(path: str) -> str:
    return f"{SOURCE_DIR}/{path}"


def extract_gql_query_from_file(file_path: str) -> str:
    if not file_path.startswith("prsload/"):
        raise ValueError(
            f"file_path must start from the root of the project, "
            f"so prsload/..., {file_path=}"
        )

    gql_query: str
    with open(_get_abs_path(file_path), encoding="utf-8") as f:
        gql_query = f.read()

    return gql_query


def parse_page_info(
    item_with_page_info: dict | None,
) -> tuple[THasMorePages, TAfterCursor]:
    if item_with_page_info is None:
        return False, None

    page_info: dict | None = safe_traverse(item_with_page_info, "pageInfo")
    if page_info is None:
        return False, None

    has_more_page: THasMorePages = page_info["hasNextPage"]
    after: TAfterCursor = page_info["endCursor"]
    return has_more_page, after
