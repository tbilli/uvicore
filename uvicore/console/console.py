import uvicore
from uvicore.console import click, group
from uvicore.console.events import command as ConsoleEvents

title_ideas = """
    A Fast Async Python Framework for CLI, Web and API

    High Performance Web, API and CLI Python Framework

    Python async Web, API and CLI fullstack Framework

    Fullstack Asynchronous Python Framework
    Python web framework
    Python Fullstack Asynchronous Web, API and CLI Framework

    Asynchronous Python Web, API and CLI Fullstack Framework

    The Async Python Framework for Craftsmen
    The Async Python Framework for Artisans
    The Artisanal Asynchronous Python Framework
"""

# Must include actual bind name when stacking decorators as it cannot deduce on its own.
# Bind decorator must come first in the stack
@uvicore.service('uvicore.console.console.cli', aliases=['Console', 'console', 'cli'])
@group(help=f"""
    \b
    Uvicore {uvicore.__version__}
    The Async Python Framework for Artisans.
    An Elegant Fullstack Python Web, API and CLI Framework

    Copyright (c) 2020 Matthew Reschke
    License http://mreschke.com/license/mit
""")
@click.version_option(version=uvicore.__version__, prog_name='Uvicore Framework', flag_value='--d')
@click.pass_context
async def cli(ctx):
    # Console startup handler
    # This runs before any command.  Even if you don't actually run a command but only display
    # the help output using NO parameters, like ./uvicore http  It does not however run when just
    # showing ./uvicore main help output.  Only on subcommand help output or actual command
    await console_startup()

    # Adding the async resource contexts gets the latest version of asyncclick to work out of the box
    context = await ctx.with_async_resource(ctx)
    context.call_on_close(console_shutdown)


    # The actual command runs right here


# Had to hack asyncclick core.py def close and __aexit__ with awaits
# github issue open, hopefully he will fix soon


async def console_startup():
    #print('console startup')
    await ConsoleEvents.Startup().codispatch()


#@cli.resultcallback()
#async def console_shutdown(result, **kwargs):
#This decorator works only if you give it an actual command
#Just showing help output from NO command does not fire this, so aiohttp still complains
#about not being shutdown properly even if you just do ./uvicore http with no actual command to run.

async def console_shutdown():
    #print('console shutdown')
    await ConsoleEvents.Shutdown().codispatch()
