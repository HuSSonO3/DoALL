import sys, os


def data_root():
    """Returns the persistent data directory.

    When running as a PyInstaller bundle (sys.frozen), data is stored
    under ~/.doall/. Otherwise, uses the project root (two levels up
    from this file).
    """
    if getattr(sys, 'frozen', False):
        root = os.path.join(os.path.expanduser('~'), 'DoALL')
    else:
        # shared.py is at project root
        root = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(root, exist_ok=True)
    return root


def db_path(*parts):
    """Path to a database file, creating parent directories."""
    path = os.path.join(data_root(), *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path
