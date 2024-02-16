import time
import sys
import uuid
from rich.console import Console as RichConsole
from rich.style import Style
from rich.table import Table
from rich import box
from typing import List


class Console(RichConsole):
    def log_error(self, msg: str):
        """Logs an error to the command line with a specific Rich Style

        Args:
            msg (str): Message to display
        """

        error_style = Style(color="red", bold=True)
        self.print(msg, style=error_style)

    def log_success(self, msg: str):
        """Logs a success to the command line with a specific Rich Style

        Args:
            msg (str): Message to display
        """

        success_style = Style(color="green", bold=True)
        self.print(msg, style=success_style)

    def log_warning(self, msg: str):
        """Logs a warning to the command line with a specific Rich Style

        Args:
            msg (str): Message to display
        """

        success_style = Style(color="yellow", bold=True)
        self.print(msg, style=success_style)

    @staticmethod
    def build_table(
        title: str, header: List[str], rows: List[List[str]], **kwargs
    ) -> Table:
        """Build a Rich table

        Args:
            title (str): Title of the table
            header (List[str]): List containing the table headers
            rows (List[List[str]]): List containing the table's columns

        Returns:
            rich.table.Table: Rich table ready to render in the command line
        """

        table = Table(title=title, box=box.SQUARE, **kwargs)

        for column in header:
            table.add_column(column)

        for row in rows:
            if len(row) != len(header):
                return "Rich table header-row mistmatch"

            table.add_row(*row)

        return table

    # Python
    BLACK = "\u001b[0;30m"
    RED = "\u001b[0;31m"
    GREEN = "\u001b[0;32m"
    BROWN = "\u001b[0;33m"
    BLUE = "\u001b[0;34m"
    PURPLE = "\u001b[0;35m"
    CYAN = "\u001b[0;36m"
    LIGHT_GRAY = "\u001b[0;37m"
    DARK_GRAY = "\u001b[1;30m"
    LIGHT_RED = "\u001b[1;31m"
    LIGHT_GREEN = "\u001b[1;32m"
    YELLOW = "\u001b[1;33m"
    LIGHT_BLUE = "\u001b[1;34m"
    LIGHT_PURPLE = "\u001b[1;35m"
    LIGHT_CYAN = "\u001b[1;36m"
    LIGHT_WHITE = "\u001b[1;37m"
    BOLD = "\u001b[1m"
    FAINT = "\u001b[2m"
    ITALIC = "\u001b[3m"
    UNDERLINE = "\u001b[4m"
    BLINK = "\u001b[5m"
    NEGATIVE = "\u001b[7m"
    CROSSED = "\u001b[9m"
    END = "\u001b[0m"


class ConsoleFold:
    def __init__(self, description):
        self._id = uuid.uuid4()
        self.description = description

    def start(self, collapsed: bool = True, colour: str = Console.GREEN):
        """Start an ANSI command line fold

        Args:
            collapsed (bool): If the fold is collapsed or not
            colour (str): ANSI color for the fold
        """

        collapse_str = "true" if collapsed else "false"
        timestamp = int(time.time())
        section = (
            "\u001b[0K"
            + f"section_start:{timestamp}:{self._id}[collapsed={collapse_str}]"
            + "\u000d\u001b[0K"
        )
        output = section + colour + self.description + Console.LIGHT_WHITE + "\u000a"
        print(output)
        sys.stdout.flush()

    def end(self):
        """End an ANSI command line fold"""

        timestamp = int(time.time())
        section = (
            "\u001b[0K" + f"section_end:{timestamp}:{self._id}" + "\u000d\u001b[0K"
        )
        print(section)
        sys.stdout.flush()


console = Console(width=130, color_system="256", highlight=False)
