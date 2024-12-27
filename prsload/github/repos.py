from dataclasses import dataclass
from typing import Generator

from prsload.github import github
from prsload.github.gql_utils import extract_gql_query_from_file


@dataclass(kw_only=True)
class Repo:
    owner: str
    name: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.name}"


def fetch_all_repos(user_login_name: str) -> Generator[Repo, None, None]:
    repo_query: str = extract_gql_query_from_file("prsload/github/repos.graphql")
    response = github.post_gql_query(
        query=repo_query, variables={"login": user_login_name}
    )

    raw_repos: list[dict] = response.data["organization"]["repositories"]["nodes"]

    for repo_data in raw_repos:
        yield Repo(
            owner=repo_data["owner"]["login"],
            name=repo_data["name"],
        )
