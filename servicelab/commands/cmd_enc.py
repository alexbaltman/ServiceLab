"""
The module contains the encrypt subcommand implemenation.
"""
import click

from servicelab.stack import pass_context
from servicelab.utils import encrypt_utils
from servicelab.utils import logger_utils
from servicelab import settings

slab_logger = logger_utils.setup_logger(settings.verbosity, 'stack.enc')


@click.command('enc',
               short_help="Encrypt a string for you to put into ccs-data.")
@click.argument('text_to_enc')
@pass_context
def cli(ctx, text_to_enc):
    """
    Encrypt a text string to be put into ccs-data.
    """
    slab_logger.info('Encrypting %s for ccs-data input' % text_to_enc)
    pkey_fname = ctx.pkey_fname()
    ret_val, ret_code = encrypt_utils.encrypt(pkey_fname, text_to_enc)
    if not ret_val:
        slab_logger.info("{} : ENC[{}]".format(text_to_enc, ret_code))
    else:
        slab_logger.error("unable to encrypt data[{}]".format(text_to_enc))
        slab_logger.error("error:\n{}".format(ret_code))
