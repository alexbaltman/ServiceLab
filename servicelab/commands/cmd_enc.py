"""
The module contains the encrypt subcommand implemenation.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import encrypt_utils


@click.command('enc',
               short_help="Encrypt a string for you to put into ccs-data.")
@click.argument('str_to_enc')
@pass_context
def cli(ctx, str_to_enc):
    """
    Encrypt a string to be put into ccs-data.

    Attributes
        ctx       -- Context object
        str_to_enc     -- the string to be encrypted
    """
    pkey_fname = ctx.pkey_fname()
    ret_val, ret_code = encrypt_utils.encrypt(pkey_fname, str_to_enc)
    if not ret_val:
        click.echo("{} : ENC[{}]".format(str_to_enc, ret_code))
    else:
        click.echo("unable to encrypt data[{}]".format(str_to_enc))
        click.echo("error:\n{}".format(ret_code))
