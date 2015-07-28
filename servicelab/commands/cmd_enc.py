import click
from servicelab.stack import pass_context
from servicelab.utils import encrypt_utils


@click.command('enc', short_help='Encrypt a value and it will give you back an \
               encrypted value for you to put into your ccs-data file.')
@click.argument('value')
@pass_context
def cli(ctx, value):
    """
    Encrypt a value to be put into ccs-data.
    """

    pkey_fname = ctx.pkey_fname()
    ret_val, ret_code = encrypt_utils.encrypt(pkey_fname, value)
    if ret_val == 0:
        print value + ": ENC[" + ret_code + "]"
    else:
        print "unable to encrypt data[" + value + "]"
        print "error :\n%s"+ret_code
