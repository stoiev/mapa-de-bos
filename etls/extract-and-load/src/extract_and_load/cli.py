"""
Main CLI module for Brazilian Police Criminal Data ETL CLI.
"""

import sys
from pathlib import Path
from typing import Optional, Any

import click
from rich.console import Console

from . import __version__
from .process_xlsx import process_xlsx
from .config import Config
from .utils import setup_logging

console = Console()


@click.command()
@click.version_option(version=__version__)
@click.argument(
    "xlsx_source", 
    default="https://www.ssp.sp.gov.br/assets/estatistica/transparencia/spDados/SPDadosCriminais_2025.xlsx"
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--sheet", "-s",
    default=0,
    help="Sheet name or index (default: 0 - first sheet)"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate compatibility without inserting data"
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Enable verbose logging"
)
def main(
    xlsx_source: str,
    config: Optional[Path] = None,
    sheet: Union[str, int] = 0,
    dry_run: bool = False,
    verbose: bool = False,
) -> None:
    """
    Brazilian Police Criminal Data ETL - Extract and load XLSX files from local disk or remote URLs.
    
    By default, processes the latest São Paulo criminal data from:
    https://www.ssp.sp.gov.br/assets/estatistica/transparencia/spDados/SPDadosCriminais_2025.xlsx
    
    You can also specify your own XLSX file or URL.
    """
    
    # Setup console logging
    setup_logging(verbose=verbose)
    
    # Load configuration
    try:
        config_obj = Config(config)
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]", file=sys.stderr)
        sys.exit(1)
    
    # Process the XLSX file
    process_xlsx(xlsx_source, sheet, dry_run, config_obj)


if __name__ == "__main__":
    main()
