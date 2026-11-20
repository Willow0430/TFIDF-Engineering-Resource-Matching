# -*- coding: utf-8 -*-
"""Root entry point for the TF-IDF engineering resource matcher.

Run from the project root:

    python main.py --report   # evaluation suite
    python main.py --demo     # interactive demo
    python main.py --web      # Gradio web demo
    python main.py --all      # tests + demo
"""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
