"""Allow `python -m SoftwareFactory.Context.CLI` to run the CLI."""

from __future__ import annotations

from . import main
import sys

if __name__ == "__main__":
    sys.exit(main())
