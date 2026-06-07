from importlib import import_module
import os
from pathlib import Path
import sys


def configure_tcl_tk():
    # Help tkinter find Tcl/Tk in regular Python and inside PyInstaller exe.
    search_roots = []

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        search_roots.append(Path(sys._MEIPASS))

    search_roots.append(Path(sys.base_prefix))

    for root in search_roots:
        tcl_path = root / "tcl" / "tcl8.6"
        tk_path = root / "tcl" / "tk8.6"

        if tcl_path.exists() and "TCL_LIBRARY" not in os.environ:
            os.environ["TCL_LIBRARY"] = str(tcl_path)

        if tk_path.exists() and "TK_LIBRARY" not in os.environ:
            os.environ["TK_LIBRARY"] = str(tk_path)


if __name__ == "__main__":
    configure_tcl_tk()
    app = import_module("src.ui.app")
    app.run_app()

