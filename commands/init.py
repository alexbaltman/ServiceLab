@click.group()
# Debug: 3
@click.option('--debug/-vvv', default=False)
# Debug: 2
@click.option('-vv', default=False)
# Debug: 1
@click.option('--verbose', '-v', is_flag=True, help='Enable debug level 1, if
              you want further debugging you use "-vv" or "-vvv/--debug"')
@click.option('--interactive', '-i', is_flag=True, help='Enables interactive
              mode for a more comprehensive engagement')
def init():
    """
    Initialize

    """
    pass


@init.command()
@click.pass_context
@click.option('', default='')
def sub():
    pass
