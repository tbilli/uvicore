import uvicore
from uvicore.package import ServiceProvider


class App1(ServiceProvider):

    def register(self) -> None:
        # Register configs
        self.configs([
            {'key': self.name, 'module': 'app1.config.app1.config'},
            {'key': 'uvicore.auth', 'module': 'app1.config.auth.config'},
        ])

    def boot(self) -> None:
        # self.tables([
        #     'mreschke.wiki.database.tables.*',
        #     #'uvicore.auth.database.tables.*',
        # ])

        # # Define data seeders used by this package
        # self.seeders([
        #     'mreschke.wiki.database.seeders.seeders.seed',
        # ])

        # # Define view and asset paths and configure the templating system
        # self.load_views()

        # Define Web and API routers
        self.load_routes()

        # # Define CLI commands to be added to the ./uvicore command line interface
        # self.load_commands()

    def load_views(self) -> None:
        """Define view and asset paths and configure the templating system
        """
        # Add view paths
        self.views(['mreschke.wiki.http.views'])

        # Add asset paths
        self.assets([
            'mreschke.wiki.http.static2',  #foundation example - BLUE
            'mreschke.wiki.http.static',     # wiki override example - RED
        ])

        def url_method(context: dict, name: str, **path_params: any) -> str:
            request = context["request"]
            return request.url_for(name, **path_params)

        def up_filter(input):
            return input.upper()

        def up_filter2(context, input):
            return input.upper()

        def is_prime(n):
            import math
            if n == 2:
                return True
            for i in range(2, int(math.ceil(math.sqrt(n))) + 1):
                if n % i == 0:
                    return False
            return True

        # Add custom template options
        self.template({
            'context_functions': [
                {'name': 'url2', 'method': url_method}
            ],
            'context_filters': [
                {'name': 'up', 'method': up_filter2}
            ],
            'filters': [
                {'name': 'up', 'method': up_filter}
            ],
            'tests': [
                {'name': 'prime', 'method': is_prime}
            ],
        })
        # Optionally, hack jinja to add anything possible like so
        #app.jinja.env.globals['whatever'] = somefunc

    def load_routes(self) -> None:
        """Define Web and API router"""
        #self.web_routes('app1.http.routes.web.Web')
        self.api_routes('app1.http.routes.api.Api')

    def load_commands(self) -> None:
        """Define CLI commands to be added to the ./uvicore command line interface"""
        group = 'wiki'
        self.commands([
            {
                'group': {
                    'name': group,
                    'parent': 'root',
                    'help': 'Wiki Commands',
                },
                'commands': [
                    {'name': 'test', 'module': 'mreschke.wiki.commands.test.cli'},
                ],
            },
            # {
            #     'group': {
            #         'name': 'db',
            #         'parent': group,
            #         'help': 'Wiki DB Commands',
            #     },
            #     'commands': [
            #         {'name': 'create', 'module': 'mreschke.wiki.commands.db.create'},
            #         {'name': 'drop', 'module': 'mreschke.wiki.commands.db.drop'},
            #         {'name': 'recreate', 'module': 'mreschke.wiki.commands.db.recreate'},
            #         {'name': 'seed', 'module': 'mreschke.wiki.commands.db.seed'},
            #     ],
            # }
        ])
