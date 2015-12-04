"""
The module contains the encrypt subcommand implemenation.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import encrypt_utils


@click.command('enc',
               short_help="Encrypt a string for you to put into ccs-data.")
@click.argument('text_to_enc')
@pass_context
def cli(ctx, text_to_enc):
    """
    Encrypt a text string to be put into ccs-data.
    """
    pkey_fname = ctx.pkey_fname()
    ret_val, ret_code = encrypt_utils.encrypt(pkey_fname, text_to_enc)
    if not ret_val:
        click.echo("{} : ENC[{}]".format(text_to_enc, ret_code))
    else:
        click.echo("unable to encrypt data[{}]".format(text_to_enc))
        click.echo("error:\n{}".format(ret_code))
