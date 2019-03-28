import errno
import os
import platform
import subprocess
import tempfile


def remove_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass


def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def write_file(filename, contents):
    with open(filename, 'w') as f:
        f.write(contents)


def read_file(filename):
    with open(filename, 'rU') as f:
        data = f.read()
        return data


def open_file(filename):
    if platform.system() == 'Darwin':  # macOS
        subprocess.call(('open', filename))
    elif platform.system() == 'Windows':  # Windows
        os.startfile(filename)
    else:  # linux variants
        subprocess.call(('xdg-open', filename))


def get_tmpdir():
    return tempfile.gettempdir()
