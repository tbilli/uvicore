import uvicore
from uvicore.typing import Dict, List, OrderedDict, get_type_hints, Tuple
from uvicore.events import Handler
from uvicore.support import module
from uvicore.support.dumper import dump, dd
from uvicore.foundation.events.app import Booted as OnAppBooted
from uvicore.contracts import Package as Package
from uvicore.console import command_is
from starlette.applications import Starlette as _Starlette
from fastapi import FastAPI as _FastAPI
from uvicore.http import response
from uvicore.http.events import server as HttpServerEvents


class Http(Handler):

    def __call__(self, event: OnAppBooted):
        """Bootstrap the HTTP Server after the Application is Booted"""

        # This will never fire if the uvicore.http module is not loaded
        # This will fire even if in console mode so we can handle showing routes
        # on certain commands.

        # Import each packages router files and add their routes to the package definition
        self.build_package_routes()

        # Fire up the HTTP server only if running from HTTP
        # Notice this is below building package routes above.  This is because
        # package routes are still built with certain CLI groups like package list and http route.
        # The server however is NOT fired up if not running a full http server command
        if not uvicore.app.is_http: return

        # Merge all packages Web and Api routes
        (web_routes, api_routes) = self.merge_routes()

        # If no routes, do nothing, no HTTP server at all
        if not web_routes and not api_routes: return

        # Fire up one or multiple HTTP servers.
        # If we have both web and api routes then we will mount subservers.
        # If not, we will only use one server.
        (base_server, web_server, api_server) = self.create_http_servers(web_routes, api_routes)

        # Add global web and api specific middleware
        self.add_middleware(web_server, api_server)

        # Get configured web and api prefixes
        web_prefix = self.get_prefix('app.web.prefix')
        api_prefix = self.get_prefix('app.api.prefix')

        # Add web routes to the web server
        self.add_web_routes(web_server, web_routes, web_prefix if not base_server else '')

        # Add api routes to the api server
        self.add_api_routes(api_server, api_routes, api_prefix if not base_server else '')

        # Add web paths (public, asset, view) and configure templates
        self.configure_webserver(web_server)

        # Fire up the proper servers and set our global app.http instance
        if base_server:
            # Running both web and api servers, we must have a perent base server
            # to mount the web and api sub servers into.  This is how we properly
            # separate web vs api middleware and other configurations.
            # Longer prefix has to be FIRST to match subapp regex properly
            if len(web_prefix) > len(api_prefix):
                base_server.mount(web_prefix, web_server)  # Web first
                base_server.mount(api_prefix, api_server)
            else:
                base_server.mount(api_prefix, api_server)  # Api first
                base_server.mount(web_prefix, web_server)
            uvicore.app._http = base_server
        elif web_server:
            # We only have a web server (no api routes)
            uvicore.app._http = web_server
        elif api_server:
            # We only have an api server (no web routes)
            uvicore.app._http = api_server

        # Attach to Starlette events and translate into Uvicore events
        @uvicore.app.http.on_event("startup")
        def startup():
            #uvicore.events.dispatch('uvicore.http.events.server.Startup')
            HttpServerEvents.Startup().dispatch()

        @uvicore.app.http.on_event("shutdown")
        def shutdown():
            #uvicore.events.dispatch('uvicore.http.events.server.Shutdown')
            HttpServerEvents.Shutdown().dispatch()


        # # Experiment add custom exceptions
        # async def internal_server_error_500(request, exc):
        #     print(exc)
        #     return response.HTML(content='custom 500 internal server error', status_code=500)

        # async def not_found_404(request, exc):
        #     print(exc)
        #     return response.HTML(content='custom 404 not found', status_code=505)
        # uvicore.app.http.server.add_exception_handler(500, internal_server_error_500)
        # uvicore.app.http.server.add_exception_handler(404, not_found_404)
        # #dump('xxxxxx', uvicore.app.http.server.exception_handlers)


        # Debug and dump the actual HTTP servers (base, web, api) info and routes
        debug_dump = False
        if debug_dump:
            dump('#################################################################')
            dump("Main HTTP Server APPLICATION", uvicore.app.http.__dict__)

            dump('#################################################################')
            dump("Main HTTP Server Routes")
            for route in uvicore.app.http.routes:
                dump(route.__dict__)

            for route in uvicore.app.http.routes:
                if route.name is None:
                    dump('#################################################################')
                    dump("Sub Server '{}' APPLICATION".format(route.path))
                    dump(route.app.__dict__)

                    dump('#################################################################')
                    dump("Sub Server '{}' Routes".format(route.path))
                    for r in route.app.router.routes:
                        dump(r.__dict__)

    def build_package_routes(self) -> None:
        """Import all packages web and api routes files and add to packages route definition"""
        for package in uvicore.app.packages.values():
            package.web.routes = self.import_package_web_routes(package)
            package.api.routes = self.import_package_api_routes(package)

    def import_package_web_routes(self, package: Package) -> Dict:
        """Import one package web routes and return routes Dict"""

        # If no routes_modules defined, nothing todo
        if not package.web.routes_module: return

        # Allow only if running as HTTP or from certain CLI commands like package list/show...
        if package.registers.web_routes and (
            uvicore.app.is_http or
            command_is('http') or
            command_is('package') or
            command_is('ioc')
        ) == False: return

        routes_module = package.web.routes_module
        prefix = package.web.prefix
        name_prefix = package.web.name_prefix

        # Import main web routes module
        routes = module.load(routes_module).object(package)

        # Get name prefix from package name plus custom name prefix
        if name_prefix:
            if name_prefix[0] == '.': name_prefix = name_prefix[1:]
            name_prefix = package.name + '.' + name_prefix
        else:
            name_prefix = package.name

        # Import the web router and create a new instance
        from uvicore.http.routing.web_router import WebRouter  # isort:skip
        router = WebRouter(package, prefix, name_prefix)

        # Get returned router with all defined routes
        router = routes.register(router)

        # Merge routes level middleware into each route
        routes_middleware = routes.middleware()
        if routes_middleware:
            for route in router.routes.values():
                route.middleware = router._merge_route_middleware(routes_middleware, route.middleware)

        # Return routes
        return router.routes

    def import_package_api_routes(self,  package: Package) -> Dict:
        """Import one package api routes and return routes Dict"""

        # If no routes_modules defined, nothing todo
        if not package.api.routes_module: return

        # Allow only if running as HTTP or from certain CLI commands like package list/show...
        if package.registers.api_routes and (
            uvicore.app.is_http or
            command_is('http') or
            command_is('package') or
            command_is('ioc')
        ) == False: return

        routes_module = package.api.routes_module
        prefix = package.api.prefix
        name_prefix = package.api.name_prefix

        # Import main web routes module
        routes = module.load(routes_module).object(package)

        # Get name prefix from package name plus custom name prefix
        if name_prefix:
            if name_prefix[0] == '.': name_prefix = name_prefix[1:]
            name_prefix = package.name + '.' + name_prefix
        else:
            name_prefix = package.name

        # Import the api router and create a new instance
        from uvicore.http.routing.api_router import ApiRouter  # isort:skip
        router = ApiRouter(package, prefix, name_prefix)

        # Get returned router with all defined routes
        router = routes.register(router)



        # Auto add all class level attribtes as middleware on each route
        # if '__annotations__' in routes.__class__.__dict__:
        #     middlewares = []
        #     for key, value in routes.__class__.__annotations__.items():
        #         middlewares.append(getattr(routes, key))

        #     for route in router.routes.values():
        #         if route.middleware is None:
        #             route.middleware = middlewares
        #         else:
        #             for middleware in middlewares:
        #                 for rmiddleware in route.middleware:
        #                     found = False
        #                     if str(rmiddleware) == str(middleware):
        #                         found = True
        #                         break
        #                 if not found:
        #                     route.middleware.append(middleware)

        #Return routes
        return router.routes

    def merge_routes(self) -> Tuple[Dict, Dict]:
        """Merge all packages web and api routes together"""
        web_routes = Dict()
        api_routes = Dict()
        for package in uvicore.app.packages.values():
            # Merging in package order ensures last package wins!
            if package.web.routes:
               web_routes.merge(package.web.routes)
            if package.api.routes:
                api_routes.merge(package.api.routes)
        return (web_routes, api_routes)

    def create_http_servers(self, web_routes, api_routes) -> Tuple[_Starlette, _FastAPI, _FastAPI]:
        """Fire up one or multiple HTTP servers"""

        # If we have both web and api routes then we will submount subservers.
        # If not, we will only use one server.
        base_server: _Starlette = None
        web_server: _FastAPI = None
        api_server: _FastAPI = None
        debug = uvicore.config('app.debug'),

        # Base server is Starlette
        if web_routes and api_routes:
            base_server = _Starlette(
                debug=debug,
            )

        # Web server is FastAPI with NO OpenAPI setup
        if web_routes:
            web_server = _FastAPI(
                debug=debug,
                version=uvicore.app.version,
                openapi_url=None,
                swagger_ui_oauth2_redirect_url=None,
            )

        # Api server is FastAPI with OpenAPI setup
        if api_routes:
            api_server = _FastAPI(
                debug=debug,
                title=uvicore.config('app.api.openapi.title'),
                version=uvicore.app.version,
                openapi_url=uvicore.config('app.api.openapi.url'),
                swagger_ui_oauth2_redirect_url=uvicore.config('app.api.openapi.docs_url') + '/oauth2-redirect',
                docs_url=uvicore.config('app.api.openapi.docs_url'),
                redoc_url=uvicore.config('app.api.openapi.redoc_url'),
                #root_path='/api',  #fixme with trying out kong
            )
        return (base_server, web_server, api_server)

    def add_middleware(self, web_server, api_server) -> None:
        """Add global web and api middleware to their respective servers"""

        # Add global web middleware
        if web_server:
            for name, middleware in uvicore.config.app.web.middleware.items():
                cls = module.load(middleware.module).object
                web_server.add_middleware(cls, **middleware.options)

        # Add global api middleware
        if api_server:
            for name, middleware in uvicore.config.app.api.middleware.items():
                cls = module.load(middleware.module).object
                api_server.add_middleware(cls, **middleware.options)

    def add_web_routes(self, web_server, web_routes, prefix) -> None:
        """Add web routes to the web server"""
        for route in web_routes.values():
            web_server.add_api_route(
                path=prefix + route.path,
                endpoint=route.endpoint,
                methods=route.methods,
                name=route.name,
                include_in_schema=False,
                response_class=response.HTML,
                dependencies=route.middleware,
            )
            # Starlette
            # web_server.add_route(
            #     path=route.path,
            #     route=route.endpoint,
            #     methods=route.methods,
            #     name=route.name,
            # )

    def add_api_routes(self, api_server, api_routes, prefix) -> None:
        """Add api routes to the api server"""
        for route in api_routes.values():
            # Get response model from parameter or infer from endpoint return type hint
            response_model = route.response_model if route.response_model else get_type_hints(route.endpoint).get('return')

            # Add route
            api_server.add_api_route(
                path=prefix + route.path,
                endpoint=route.endpoint,
                methods=route.methods,
                name=route.name,
                response_model=response_model,
                tags=route.tags,
                dependencies=route.middleware,
            )

    def configure_webserver(self, web_server) -> None:
        """Configure the webserver with public, asset and view paths and template options"""

        # Loop each package with an HTTP definition and add to our HTTP server
        public_paths = []
        asset_paths = []
        view_paths = []
        template_options = Dict()
        for package in uvicore.app.packages.values():
            #if not 'http' in package: continue
            if not 'web' in package: continue

            # Append public paths for later
            for path in package.web.public_paths:
                path_location = module.location(path)
                if path_location not in public_paths: public_paths.append(path_location)

            # Append asset paths for later
            for path in package.web.asset_paths:
                path_location = module.location(path)
                if path_location not in asset_paths: asset_paths.append(path_location)

            # Append template paths
            for path in package.web.view_paths or []:
                view_paths.append(path)

            # Deep merge template options
            template_options.merge(package.web.template_options or {})

        # Mount all static paths
        self.mount_static(web_server, public_paths, asset_paths)

        # Initialize new template environment from the options above
        self.initialize_templates(view_paths, template_options)

    def mount_static(self, web_server, public_paths: List, asset_paths: List) -> None:
        """Mount static routes defined in all packages"""
        StaticFiles = uvicore.ioc.make('uvicore.http.static.StaticFiles')

        # Mount all asset paths
        # Last directory defined WINS, which fits our last provider wins
        asset_url = uvicore.config.app.asset.path or '/assets'
        web_server.mount(asset_url, StaticFiles(directories=asset_paths), name='assets')

        # Mount all public paths (always at /)
        # Since it is root / MUST be defined last or it wins above any path after it
        web_server.mount('/', StaticFiles(directories=public_paths), name='public')

    def initialize_templates(self, paths, options) -> None:
        """Initialize and configure template system"""
        # Get the template singleton from the IoC
        templates = uvicore.ioc.make('uvicore.http.templating.jinja.Jinja')

        # Add all packages view paths
        for path in paths:
            templates.include_path(module.location(path))

        # Add all packages deep_merged template options
        if 'context_functions' in options:
            for name, method in options['context_functions'].items():
                templates.include_context_function(name, method)
        if 'context_filters' in options:
            for name, method in options['context_filters'].items():
                templates.include_context_filter(name, method)
        if 'filters' in options:
            for name, method in options['filters'].items():
                templates.include_filter(name, method)
        if 'tests' in options:
            for name, method in options['tests'].items():
                templates.include_test(name, method)

        # Initialize template system
        templates.init()

    def get_prefix(self, confpath) -> str:
        """Get configured web and api prefixes ensuring "" prefix and no trailing /, or / if blank)"""
        prefix = uvicore.config(confpath)
        #if not prefix: prefix = '/'
        #if prefix != '/' and prefix[-1] == '/': prefix = prefix[0:-1]  # No trailing /
        if prefix and prefix[-1] == '/': prefix = prefix[0:-1]  # No trailing /
        return prefix
