import uvicore
from uvicore.typing import Dict, Callable, ASGIApp, Send, Receive, Scope
from uvicore.http.response import Text, HTML, JSON, Response
from uvicore.http.request import HTTPConnection, Request
from uvicore.support.dumper import dump, dd
from uvicore.support import module
from uvicore.http.exceptions import HTTPException
from uvicore.contracts import Authenticator, User, UserProvider


@uvicore.service()
class Authentication:
    """Authentication global middleware capable of multiple authenticator backends"""

    def __init__(self, app: ASGIApp, route_type: str) -> None:
        # __init__ called one time on uvicore HTTP bootstrap
        # __call__ called on every request
        self.app = app
        self.route_type = str(route_type or 'api').lower()
        assert self.route_type in ['web', 'api']

        # Load and merge the auth config for this route type (web or api)
        self.config = self.load_config()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Middleware only for http and websocket types
        if scope["type"] not in ["http", "websocket"]:
            # Next middleware in stack
            await self.app(scope, receive, send)
            return

        # Get the http connection.  This is essentially the Request but not HTTP specific.
        # The base connection that works for HTTP and WebSockets.  Request inherits from HTTPConnection
        request = HTTPConnection(scope)

        # Loop each authenticator
        user = None
        for authenticator in self.config.authenticators.values():
            # Load authenticator backend
            try:
                backend: Authenticator = module.load(authenticator.module).object(authenticator)
            except Exception as e:
                raise Exception('Issue trying to import authenticator module defined in app.auth config - {}'.format(str(e)))

            # Call backend authenticate() method
            user: User = await backend.authenticate(request)

            # Check for exception and return
            # NO, authenticators should NEVER return errors, only valid User or None
            # if isinstance(user, HTTPException):
            #     return await self.error_response(user, scope, receive, send)

            # If user found, stop authenticator itteration
            if user is not None: break


        # If all authenticators returned None, user is not logged in with any method.
        # Build an anonymouse user object to inject into the request scope
        if user is None:
            anonymous_provider: UserProvider = module.load(self.config.default_provider.module).object()
            params = self.config.default_provider.options.clone()
            params.merge(self.config.default_provider.anonymous_options)
            provider_method = anonymous_provider.retrieve_by_username
            if 'id' in params: provider_method = anonymous_provider.retrieve_by_id
            if 'uuid' in params: provider_method = anonymous_provider.retrieve_by_uuid
            user = await provider_method(request=request, **params)

        # Add user to request
        scope["user"] = user
        scope["auth"] = user.permissions

        # Next middleware in stack
        await self.app(scope, receive, send)

    def load_config(self):
        """Get web or api auth config and merge default options and providers"""

        # Load all default option configs
        default_options = uvicore.config.app.auth.default_options

        # Load all provider configs
        providers = uvicore.config.app.auth.providers

        # Merge default options and providers into each authenticator
        config_path = 'app.auth.api'
        if self.route_type == 'web': config_path = 'app.auth.web'
        config = uvicore.config.dotget(config_path).clone()

        # Merge provider Dict if specified as a string
        if 'default_provider' in config and isinstance(config.default_provider, str):
            if config.default_provider in providers:
                config.default_provider = providers[config.default_provider].clone()
            else:
                raise Exception("Default options '{}' not found in auth config".format(config.default_provider))

        # Merge each providers configuration
        for authenticator in config.authenticators.values():

            # Merge default_options Dict if specified as a string
            if 'default_options' in authenticator:
                # Deep merge default options
                if authenticator.default_options in default_options:
                    authenticator.defaults(default_options[authenticator.default_options])  # Defaults does a clone!
                else:
                    raise Exception("Default options '{}' not found in auth config".format(authenticator.default_options))

            # If no provider specified, use default_provider (already a full Dict from above)
            if 'provider' not in authenticator:
                authenticator.provider = config.default_provider

            # Merge provider Dict if specified as a string
            if 'provider' in authenticator and isinstance(authenticator.provider, str):
                if authenticator.provider in providers:
                    authenticator.provider = providers[authenticator.provider].clone()
                else:
                    raise Exception("Provider '{}' not found in auth config".format(authenticator.provider))

        # Returned merge config for all authenticators
        return config

    async def error_response_OBSOLETE(self, user: User, scope: Scope, receive: Receive, send: Send):
        """Build and return error response"""
        if self.route_type == 'web':
            # Fixme, how can I use the user customized 401 HTML?
            response = HTML(
                content='401 HTML here? - {}'.format(user.detail),
                status_code=user.status_code,
                headers=user.headers
            )
        else:
            response = JSON(
                content={'message': user.detail},
                status_code=user.status_code,
                headers=user.headers
            )
        if scope["type"] == "websocket":
            await send({"type": "websocket.close", "code": 1000})
        else:
            await response(scope, receive, send)
        return
























# import typing

# from starlette.authentication import (
#     AuthCredentials,
#     AuthenticationBackend,
#     AuthenticationError,
#     UnauthenticatedUser,
# )
# from starlette.requests import HTTPConnection
# from starlette.responses import PlainTextResponse, Response
# from starlette.types import ASGIApp, Receive, Scope, Send


# class AuthenticationMiddleware:
#     def __init__(
#         self,
#         app: ASGIApp,
#         backend: AuthenticationBackend,
#         on_error: typing.Callable[
#             [HTTPConnection, AuthenticationError], Response
#         ] = None,
#     ) -> None:
#         self.app = app
#         self.backend = backend
#         self.on_error = (
#             on_error if on_error is not None else self.default_on_error
#         )  # type: typing.Callable[[HTTPConnection, AuthenticationError], Response]

#     async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
#         if scope["type"] not in ["http", "websocket"]:
#             await self.app(scope, receive, send)
#             return

#         conn = HTTPConnection(scope)
#         try:
#             auth_result = await self.backend.authenticate(conn)
#         except AuthenticationError as exc:
#             response = self.on_error(conn, exc)
#             if scope["type"] == "websocket":
#                 await send({"type": "websocket.close", "code": 1000})
#             else:
#                 await response(scope, receive, send)
#             return

#         if auth_result is None:
#             auth_result = AuthCredentials(), UnauthenticatedUser()
#         scope["auth"], scope["user"] = auth_result
#         await self.app(scope, receive, send)

#     @staticmethod
#     def default_on_error(conn: HTTPConnection, exc: Exception) -> Response:
#         return PlainTextResponse(str(exc), status_code=400)
