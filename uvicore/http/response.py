from os import stat
import re
import uvicore
from uvicore.typing import Dict
from uvicore.support.dumper import dump
from uvicore.support.module import load
from uvicore.http.request import Request
from starlette.templating import _TemplateResponse
from starlette.background import BackgroundTask as _BackgroundTask

# Proxy starlette response APIs
from starlette.responses import Response
from starlette.responses import PlainTextResponse as Text
from starlette.responses import HTMLResponse as HTML
from starlette.responses import JSONResponse as JSON
from fastapi.responses import UJSONResponse as UJSON
from fastapi.responses import ORJSONResponse as ORJSON
from starlette.responses import RedirectResponse as Redirect
from starlette.responses import StreamingResponse as Stream
from starlette.responses import FileResponse as File

# Get our current template system from the IoC
templates = uvicore.ioc.make('uvicore.http.templating.jinja.Jinja')
#templates = uvicore.ioc.make('Templates') # Fixme when you impliment other templating engines, if ever

@uvicore.service()
async def View(
    name: str,
    context: dict = {},
    status_code: int = 200,
    headers: dict = None,
    media_type: str = None,
    background: _BackgroundTask = None,
) -> _TemplateResponse:

    # Pull request out of context (which is always present as it is required for response.View())
    request: Request = context.get('request');

    # Check for a view composer when rendering this view
    view_name = name.split('.')[0]
    context = Dict(context)
    for (composer_module, composer_views) in uvicore.config.uvicore.http.view_composers.items():
        for composer_view in composer_views:
            if (composer_view == '*'): composer_view = '.*'
            if re.search(composer_view, view_name):
                try:
                    # Load composer and merge the return using .defaults() to ensure
                    # the view wins in the override battle over the composer
                    composer = load(composer_module).object(request, name, context, status_code, headers, media_type)
                    context.defaults(await composer.compose())
                except Exception as e:
                    # Composer not found, silently ignore
                    #dump(e)
                    pass

    # Renger the template
    return templates.TemplateResponse(
        name=name,
        context=context,
        status_code=status_code,
        headers=headers,
        media_type=media_type,
        background=background
    )
