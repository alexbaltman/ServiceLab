"""
The module contains the encrypt subcommand implemenation.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import encrypt_utils


@click.command('enc',
               short_help="Encrypt a value for you to put into your ccs-data file.")
@click.argument('value')
@pass_context
def cli(ctx, value):
    """
    Encrypt a value to be put into ccs-data.

    Attributes
        ctx       -- Context object
        value     -- the string to be encrypted
    """

    pkey_fname = ctx.pkey_fname()
    ret_val, ret_code = encrypt_utils.encrypt(pkey_fname, value)
    if not ret_val:
        click.echo("{} : ENC[{}]".format(value, ret_code))
    else:
        click.echo("unable to encrypt data[{}]".format(value))
        click.echo("error:\n{}".format(ret_code))
