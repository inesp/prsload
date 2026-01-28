class PRAnalyticsError(Exception):
    """Base exception class for PR Analytics application"""


class SettingsError(PRAnalyticsError):
    """Raised when configuration/settings are invalid"""


class GitHubException(PRAnalyticsError):
    def __init__(
        self,
        msg: str,
        gql_errors: list[dict] | None = None,
        query: str | None = None,
        variables: dict | None = None,
    ):
        self.gql_errors = gql_errors
        self.query = query
        self.variables = variables

        if user_msgs := self.user_error_desc():
            msg = f"{msg} {user_msgs}"

        super().__init__(msg)

    def _user_error_desc(self) -> str:
        if self.gql_errors:
            return ", ".join([str(e) for e in self.gql_errors])
        return ""
