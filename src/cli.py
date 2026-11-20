# -*- coding: utf-8 -*-
"""Command-line entry point.

Usage::

    python main.py            # run the evaluation suite (default)
    python main.py --report   # same as above
    python main.py --demo     # interactive demo
    python main.py --web      # launch the Gradio web demo
    python main.py --all      # run tests then the demo
"""

import sys


def _fix_windows_console():
    """Force UTF-8 stdout on Windows so Chinese output is not garbled."""
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    _fix_windows_console()

    from .evaluation import run_full_tests, demonstrate
    from .web import build_web_demo

    if not argv:
        run_full_tests(verbose=True)
    elif argv[0] == "--report":
        run_full_tests(verbose=True)
    elif argv[0] == "--demo":
        demonstrate()
    elif argv[0] == "--web":
        build_web_demo()
    elif argv[0] == "--all":
        run_full_tests(verbose=True)
        print("\n\n")
        demonstrate()
    else:
        print("Unknown argument: %s" % argv[0])
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
