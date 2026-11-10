"""Frozen entry point for the independent camera-only node."""

import multiprocessing

multiprocessing.freeze_support()

from zerith_h1_pro.camera_main import main

if __name__ == "__main__":
    main()
