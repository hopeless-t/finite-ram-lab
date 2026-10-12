from __future__ import annotations

import sys


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command is not None:
        from .fast_cli import FAST_COMMANDS

        if command in FAST_COMMANDS:
            from .fast_cli import main as fast_main

            fast_main()
            return
    from .cli import main as full_main

    full_main()


if __name__ == "__main__":
    main()
