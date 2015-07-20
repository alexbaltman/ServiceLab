from contextlib import contextmanager
import tempfile
import shutil


@contextmanager
def temporary_dir(root_dir=None, cleanup=True):
    pth = tempfile.mkdtemp(dir=root_dir)
    try:
        yield pth
    finally:
        if cleanup:
            shutil.rmtree(pth, ignore_errors=True)
