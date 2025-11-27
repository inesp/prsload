import logging

from flask import Flask
from flask import render_template

from prsload.exceptions import PRAnalyticsError
from prsload.extensions import register_template_filters
from prsload.routes.data_fetcher import data_fetcher_bp
from prsload.routes.home import home_bp
from prsload.routes.top_reviewers import analytics_bp

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s %(asctime)s %(message)s",
)


def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(data_fetcher_bp)

    # Register template filters
    register_template_filters(app)

    # Register error handlers
    @app.errorhandler(PRAnalyticsError)
    def handle_analytics_error(error):
        """Handle all PR Analytics specific errors"""
        logger.error(f"PR Analytics error: {error}")
        return (
            render_template(
                "error.html",
                title="Application Error",
                error_message=str(error),
                error_type=type(error).__name__,
            ),
            500,
        )

    @app.errorhandler(400)
    @app.errorhandler(401)
    @app.errorhandler(403)
    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(406)
    @app.errorhandler(408)
    @app.errorhandler(409)
    @app.errorhandler(410)
    @app.errorhandler(413)
    @app.errorhandler(414)
    @app.errorhandler(415)
    @app.errorhandler(429)
    def handle_client_errors(error):
        """Handle all 4XX client errors"""
        error_messages = {
            400: ("Bad Request", "The request could not be understood by the server."),
            401: (
                "Unauthorized",
                "You need to be authenticated to access this resource.",
            ),
            403: ("Forbidden", "You don't have permission to access this resource."),
            404: (
                "Page Not Found",
                "The page you're looking for doesn't exist. It might have been moved, deleted, "
                "or you entered the wrong URL.",
            ),
            405: (
                "Method Not Allowed",
                "The HTTP method is not allowed for this resource.",
            ),
            406: (
                "Not Acceptable",
                "The server cannot produce a response matching the client's accept headers.",
            ),
            408: ("Request Timeout", "The server timed out waiting for the request."),
            409: (
                "Conflict",
                "The request conflicts with the current state of the resource.",
            ),
            410: (
                "Gone",
                "The resource is no longer available and will not be available again.",
            ),
            413: (
                "Payload Too Large",
                "The request payload is too large for the server to process.",
            ),
            414: (
                "URI Too Long",
                "The URI provided was too long for the server to process.",
            ),
            415: (
                "Unsupported Media Type",
                "The media type of the request is not supported.",
            ),
            429: (
                "Too Many Requests",
                "You have sent too many requests in a short period of time.",
            ),
        }

        error_title, error_message = error_messages.get(
            error.code, ("Client Error", "An error occurred with your request.")
        )

        return (
            render_template(
                "404.html",
                title=f"{error.code} {error_title}",
                error_code=error.code,
                error_title=error_title,
                error_message=error_message,
                show_header_title=False,
            ),
            error.code,
        )

    @app.errorhandler(500)
    def handle_server_error(error):
        """Handle generic server errors"""
        logger.error(f"Server error: {error}")
        return (
            render_template(
                "error.html",
                title="Server Error",
                error_message="An unexpected error occurred",
            ),
            500,
        )

    return app


# For direct execution
app = create_app()
