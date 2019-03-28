import traceback
import sys
import click

_is_interactive = True


def set_interactive(x_is_interactive):
    global _is_interactive
    _is_interactive = x_is_interactive


def is_interactive():
    if not is_tty():
        return False

    return _is_interactive


def is_tty():
    return sys.__stdout__.isatty()


def yellow_bold(text):
    return click.style(str(text), fg='yellow', bold=True)


def blue_bold(text):
    return click.style(str(text), fg='blue', bold=True)


def red_bold(text):
    return click.style(str(text), fg='red', bold=True)


def error(text):
    output('{} {}'.format(red_bold('ERROR!'), text))


def important(msg):
    click.echo('{} {}'.format(blue_bold('!'), msg))


def output(text):
    click.echo('> {}'.format(text))


def exception_format(err):
    tb = traceback.format_exc()
    error('{}\n{}\nThe process will not continue - Exiting.'.format(err, tb))
