import os

# Unknown or badly-typed props raise instead of logging a warning (see afik/core/contract.py).
os.environ.setdefault("AFIK_STRICT_PROPS", "1")
