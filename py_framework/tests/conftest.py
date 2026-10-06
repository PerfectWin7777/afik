import os

# Unknown or badly-typed props raise instead of logging a warning (see pyflutter/core/contract.py).
os.environ.setdefault("PYFLUTTER_STRICT_PROPS", "1")
