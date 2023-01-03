import os

# If using installed version of asyncclick
#import asyncclick as click
#from asyncclick.termui import _ansi_colors, _ansi_reset_all

# If using local copy of asyncclick
import asyncclick as click
from asyncclick.termui import _ansi_colors, _ansi_reset_all



# MIT License

# Copyright (c) 2016 Roman Tonkonozhko

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# See https://github.com/uvicore/click-help-colors



class HelpColorsException(Exception):
    pass


def _colorize(text, color=None):
    if not color or "NO_COLOR" in os.environ:
        return text
    try:
        return '\033[%dm' % (_ansi_colors[color]) + text + _ansi_reset_all
    except KeyError:
        raise HelpColorsException('Unknown color %r' % color)


def _extend_instance(obj, cls):
    """Apply mixin to a class instance after creation"""
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (cls, base_cls), {})


class HelpColorsFormatter(click.HelpFormatter):
    def __init__(self, headers_color=None, options_color=None,
                 options_custom_colors=None, *args, **kwargs):
        self.headers_color = headers_color
        self.options_color = options_color
        self.options_custom_colors = options_custom_colors
        super(HelpColorsFormatter, self).__init__(*args, **kwargs)

    def _pick_color(self, option_name):
        opt = option_name.split()[0]
        if (self.options_custom_colors and
                (opt in self.options_custom_colors.keys())):
            return self.options_custom_colors[opt]
        else:
            return self.options_color

    def write_usage(self, prog, args='', prefix='Usage: '):
        colorized_prefix = _colorize(prefix, color=self.headers_color)
        super(HelpColorsFormatter, self).write_usage(prog, args, prefix=colorized_prefix)

    def write_heading(self, heading):
        colorized_heading = _colorize(heading, color=self.headers_color)
        super(HelpColorsFormatter, self).write_heading(colorized_heading)

    def write_dl(self, rows, **kwargs):
        colorized_rows = [(_colorize(row[0], self._pick_color(row[0])), row[1]) for row in rows]
        super(HelpColorsFormatter, self).write_dl(colorized_rows, **kwargs)


class HelpColorsMixin(object):
    def __init__(self, help_headers_color=None, help_options_color=None, help_options_custom_colors=None, *args, **kwargs):
        self.help_headers_color = help_headers_color
        self.help_options_color = help_options_color
        self.help_options_custom_colors = help_options_custom_colors
        super(HelpColorsMixin, self).__init__(*args, **kwargs)

    def get_help(self, ctx):
        formatter = HelpColorsFormatter(
            width=ctx.terminal_width,
            max_width=ctx.max_content_width,
            headers_color=self.help_headers_color,
            options_color=self.help_options_color,
            options_custom_colors=self.help_options_custom_colors)
        self.format_help(ctx, formatter)
        return formatter.getvalue().rstrip('\n')


class HelpColorsGroup(HelpColorsMixin, click.Group):
    def __init__(self, *args, **kwargs):
        super(HelpColorsGroup, self).__init__(*args, **kwargs)

    def command(self, *args, **kwargs):
        kwargs.setdefault('cls', HelpColorsCommand)
        kwargs.setdefault('help_headers_color', self.help_headers_color)
        kwargs.setdefault('help_options_color', self.help_options_color)
        kwargs.setdefault('help_options_custom_colors', self.help_options_custom_colors)
        return super(HelpColorsGroup, self).command(*args, **kwargs)

    def group(self, *args, **kwargs):
        kwargs.setdefault('cls', HelpColorsGroup)
        kwargs.setdefault('help_headers_color', self.help_headers_color)
        kwargs.setdefault('help_options_color', self.help_options_color)
        kwargs.setdefault('help_options_custom_colors', self.help_options_custom_colors)
        return super(HelpColorsGroup, self).group(*args, **kwargs)


class HelpColorsCommand(HelpColorsMixin, click.Command):
    def __init__(self, *args, **kwargs):
        super(HelpColorsCommand, self).__init__(*args, **kwargs)


class HelpColorsMultiCommand(HelpColorsMixin, click.MultiCommand):
    def __init__(self, *args, **kwargs):
        super(HelpColorsMultiCommand, self).__init__(*args, **kwargs)

    def resolve_command(self, ctx, args):
        cmd_name, cmd, args[1:] = super(HelpColorsMultiCommand, self).resolve_command(ctx, args)

        if not isinstance(cmd, HelpColorsMixin):
            if isinstance(cmd, click.Group):
                _extend_instance(cmd, HelpColorsGroup)
            if isinstance(cmd, click.Command):
                _extend_instance(cmd, HelpColorsCommand)

        if not getattr(cmd, 'help_headers_color', None):
            cmd.help_headers_color = self.help_headers_color
        if not getattr(cmd, 'help_options_color', None):
            cmd.help_options_color = self.help_options_color
        if not getattr(cmd, 'help_options_custom_colors', None):
            cmd.help_options_custom_colors = self.help_options_custom_colors

        return cmd_name, cmd, args[1:]
