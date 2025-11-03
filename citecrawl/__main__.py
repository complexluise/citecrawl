import sys
from rich.console import Console
from rich.logging import RichHandler
import logging
from citecrawl.cli import cli

if __name__ == '__main__':
    log = logging.getLogger("rich")
    console = Console(file=sys.stdout)
    handler = RichHandler(console=console, rich_tracebacks=True, show_path=False)
    log.addHandler(handler)
    cli()
