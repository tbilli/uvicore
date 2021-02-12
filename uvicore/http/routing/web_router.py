from __future__ import annotations
import uvicore
from uvicore.typing import Any, Callable, List, Dict, Optional
from uvicore.http.routing.router import Router
from uvicore.support.dumper import dump, dd
from uvicore.contracts import WebRoute as RouteInterface
from prettyprinter import pretty_call, register_pretty


@uvicore.service()
class WebRouter(Router['WebRoute']):

    def get(self, path: str,
        endpoint: Optional[Callable] = None,
        *,
        name: Optional[str] = None,
        autoprefix: bool = True
    ):
        # Build parameters
        methods = ['GET']
        #params = {key:value for key, value in locals().items() if key != 'self'}
        params = locals()
        params.pop('self')

        # Pass to generic add method
        return self.add(**params)


    def add(self,
        path: str,
        endpoint: Optional[Callable] = None,
        methods: List[str] = ['GET'],
        *,
        name: Optional[str] = None,
        autoprefix: bool = True
    ):
        """Generic add method and decorator"""

        # Clean path and name
        (name, full_path, name, full_name) = self._clean_add(path, name, autoprefix)

        def handle(endpoint):
            # Create route SuperDict
            route = WebRoute({
                'path': full_path,
                'name': full_name,
                'endpoint': endpoint,
                'methods': methods,
                'original_path': path,
                'original_name': name,
            })
            self.routes[full_name] = route
            return route

        # Method access
        if endpoint: return handle(endpoint)

        # Decorator Access
        def decorator(func):
            handle(func)
            return func
        return decorator


@uvicore.service()
class WebRoute(RouteInterface):
    """Route superdict definition"""
    pass


@register_pretty(WebRoute)
def pretty_entity(value, ctx):
    """Custom pretty printer for my SuperDict"""
    # This printer removes the class name uvicore.types.Dict and makes it print
    # with a regular {.  This really cleans up the output!

    # SuperDict are printed as Dict, but this Package SuperDict should
    # be printed more like a class with key=value notation, so use **values
    return pretty_call(ctx, 'WebRoute', **value)
















# # Example of using FastAPI router even for Web routes
# @uvicore.service()
# class WebRouterX(ApiRouter):

#     def get(
#         self,
#         path: str,
#         *,
#         #response_model: Optional[Type[Any]] = None,
#         status_code: int = 200,
#         #tags: Optional[List[str]] = None,
#         dependencies: Optional[Sequence[params.Depends]] = None,
#         #summary: Optional[str] = None,
#         #description: Optional[str] = None,
#         #response_description: str = "Successful Response",
#         #responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
#         #deprecated: Optional[bool] = None,
#         #operation_id: Optional[str] = None,
#         #response_model_include: Optional[Union[SetIntStr, DictIntStrAny]] = None,
#         #response_model_exclude: Optional[Union[SetIntStr, DictIntStrAny]] = None,
#         #response_model_by_alias: bool = True,
#         #response_model_exclude_unset: bool = False,
#         #response_model_exclude_defaults: bool = False,
#         #response_model_exclude_none: bool = False,
#         #include_in_schema: bool = False,  # Uvicore change
#         #response_class: Type[Response] = Default(JSONResponse),
#         name: Optional[str] = None,
#         #callbacks: Optional[List[BaseRoute]] = None,
#     ) -> Callable[[DecoratedCallable], DecoratedCallable]:
#         return super().get(
#             path=path,
#             #response_model=response_model,
#             status_code=status_code,
#             #tags=tags,
#             dependencies=dependencies,
#             #summary=summary,
#             #description=description,
#             #response_description=response_description,
#             #responses=responses,
#             #deprecated=deprecated,
#             #operation_id=operation_id,
#             #response_model_include=response_model_include,
#             #response_model_exclude=response_model_exclude,
#             #response_model_by_alias=response_model_by_alias,
#             #response_model_exclude_unset=response_model_exclude_unset,
#             #response_model_exclude_defaults=response_model_exclude_defaults,
#             #response_model_exclude_none=response_model_exclude_none,
#             include_in_schema=False,  # Don't show in openapi docs
#             response_class=response.HTML,
#             name=name,
#             #callbacks=callbacks,
#         )



# # Example of just using the entier Starlette Router without abstraction
# @uvicore.service()
# class WebRouterXX(_StarletteRouter):

#     # Add a GET route decorator to starlette
#     def get(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['GET'],
#             include_in_schema=False,
#         )

#     # Add a POST route decorator to starlette
#     def post(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['POST'],
#             include_in_schema=False,
#         )

#     # Add a PUT route decorator to starlette
#     def put(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['PUT'],
#             include_in_schema=False,
#         )

#     # Add a PATCH route decorator to starlette
#     def patch(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['PATCH'],
#             include_in_schema=False,
#         )

#     # Add a DELETE route decorator to starlette
#     def delete(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['DELETE'],
#             include_in_schema=False,
#         )

#     # Add a OPTIONS route decorator to starlette
#     def options(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['OPTIONS'],
#             include_in_schema=False,
#         )

#     # Add a HEAD route decorator to starlette
#     def head(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['HEAD'],
#             include_in_schema=False,
#         )

#     # Add a TRACE route decorator to starlette
#     def trace(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self.route(
#             path=path,
#             name=name,
#             methods=['TRACE'],
#             include_in_schema=False,
#         )

#     def include_router(self, router: "WebRouter") -> None:
#         # Starlette does not have a _router.include_router  like FastAPI
#         # This manually adds each route in the router to starlette router
#         # Used in the Class Based Controllers _init_cbv code
#         for route in router.routes:
#             self.routes.append(route)




# # Example of making my own router abstraction
# class WebRouterXXX(RouterInterface):

#     @property
#     def router(self) -> _StarletteRouter:
#         return self._router

#     @property
#     def routes(self) -> List[BaseRoute]:
#         return self._router.routes

#     @property
#     def on_startup(self) -> None:
#         return self._router.on_startup

#     @property
#     def on_shutdown(self) -> None:
#         return self._router.on_shutdown

#     def __init__(self):
#         # Fireup Starlette Router
#         self._router = _StarletteRouter()

#     def get(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self._router.route(
#             path=path,
#             name=name,
#             methods=['GET']
#         )

#     def post(self,
#         path: str,
#         name: str = None,
#     ) -> Callable:
#         return self._router.route(
#             path=path,
#             name=name,
#             methods=['POST']
#         )

#     # Not needed - was used for Class Based Controllers
#     # def include_router(self, router: "WebRouter") -> None:
#     #     # Starlette does not have a _router.include_router  like FastAPI
#     #     # This manually adds each route in the router to starlette router
#     #     for route in router.routes:
#     #         self._router.routes.append(route)


# # IoC Class Instance
# #WebRouter: RouterInterface = uvicore.ioc.make('WebRouter', _WebRouter)

# # Public API for import * and doc gens
# #__all__ = ['WebRouter', '_WebRouter']
