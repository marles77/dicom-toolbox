# ==========================================================
# DICOM manager
# Author: Marcin Leśniak, PhD
#
# Constants
# ==========================================================

import os
from tkinter import Misc
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import MessageDialog, Querybox, QueryDialog
from ttkbootstrap.constants import RIGHT, BOTTOM, X, S
#from ttkbootstrap.localization import MessageCatalog
from typing import Optional, Tuple, Any


class Constants:
    APP_TITLE = "Dicom Toolbox"
    APP_THEME = "gruvbox-light"
    CURR_DIR = os.getcwd()
    BG_COLOR = "#CFD8DC"
    WINDOW_SIZE = (1200, 600)
    SETTINGS_PATH = 'extra/settings.json'
    AUTHOR = "Marcin Leśniak"
    VERSION = "0.1.0"

class Caps:
    CAP_YES = "Tak"
    CAP_YES_ALL = "Tak na wszystkie"
    CAP_NO = "Nie"
    CAP_CANCEL = "Anuluj"
    CAP_OK = "OK"
    #CAP_UNDERSTAND


class PLMessageDialog(MessageDialog):

    def __init__(self, message, title=" ", buttons=None, command=None, parent=None):
        super().__init__(
            message=message,
            title=title,
            buttons=buttons or [Caps.CAP_CANCEL, Caps.CAP_NO, Caps.CAP_YES],
            command=command,
            parent=parent,
        )
    def on_button_press(self, button: ttk.Button) -> None:
        """Save result, close dialog, and execute command."""

        self._result = button["text"]
        command = self._command

        self._toplevel.destroy()

        if command is not None:
            command()


class PLWarning(MessageDialog):

    def __init__(self, message, title=" ", command=None, parent=None):
        super().__init__(
            message=message,
            title=title,
            buttons=[Caps.CAP_OK],
            command=command,
            parent=parent,
        )


class PLQueryDialog(QueryDialog):

    def create_buttonbox(self, master):
        """Build the Submit/Cancel button row."""
        frame = ttk.Frame(master, padding=(5, 10))
        
        submit = ttk.Button(
            master=frame,
            bootstyle="primary",
            text=Caps.CAP_OK,
            command=self.on_submit,
        )
        submit.pack(padx=2, side=RIGHT)
        submit.lower()
        
        cancel = ttk.Button(
            master=frame,
            text=Caps.CAP_CANCEL,
            command=self.on_cancel,
        )
        cancel.pack(padx=2, side=RIGHT)
        cancel.lower()
        
        ttk.Separator(self._toplevel).pack(fill=X)
        frame.pack(side=BOTTOM, fill=X, anchor=S)

class PLQuerybox(Querybox):

    @staticmethod
    def get_string(
            prompt: str = "",
            title: str = " ",
            initialvalue: Optional[str] = None,
            parent: Optional[Misc] = None,
            *,
            position: Optional[Tuple[int, int]] = None,
            **kwargs: Any,
    ) -> Optional[str]:
        """Prompt for a string. Returns the text, or ``None`` if cancelled.

        Note: submitting an empty field returns ``""`` (distinct from the
        ``None`` returned on cancel).
        """
        initialvalue = initialvalue or ""
        dialog = PLQueryDialog(prompt, title, initialvalue, parent=parent, **kwargs)
        dialog.show(position)
        return dialog.result


