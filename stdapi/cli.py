"""
StdAPI CLI Wrapper
Forwards execution to the unified stdapi.ui.cli entrypoint.
"""
from .ui.cli import main

if __name__ == "__main__":
    main()
