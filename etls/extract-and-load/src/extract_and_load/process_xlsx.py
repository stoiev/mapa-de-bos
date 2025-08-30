"""
Extract functions for Brazilian police criminal data ETL operations.
"""

import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from urllib.request import urlretrieve

import click
import pandas as pd
import requests
from rich.console import Console
from rich.table import Table
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError

from .config import Config

console = Console()

ERROR_MSG_TRUNCATE_LENGTH = 1000

def process_xlsx(
    xlsx_source: str,
    sheet: Union[str, int] = 0,
    dry_run: bool = False,
    config: Optional[Config] = None
) -> None:
    """Process Brazilian criminal data from XLSX file (local or remote) and load to database."""
    temp_file_path = None  # Track temporary file for cleanup
    
    try:
        # Determine if source is URL or local file
        parsed_url = urlparse(xlsx_source)
        is_url = bool(parsed_url.scheme and parsed_url.netloc)
        
        if is_url:
            console.print(f"[blue]Downloading XLSX file from:[/blue] {xlsx_source}")
            xlsx_file = _download_xlsx_file(xlsx_source)
            temp_file_path = xlsx_file  # Downloaded file needs cleanup
            table = Path(xlsx_source).stem.lower().replace(" ", "_").replace("-", "_")
        else:
            xlsx_file = Path(xlsx_source)
            if not xlsx_file.exists():
                console.print(f"[red]Error:[/red] File {xlsx_source} does not exist")
                return
            table = xlsx_file.stem.lower().replace(" ", "_").replace("-", "_")
        
        console.print(f"[blue]Processing Brazilian police XLSX file:[/blue] {xlsx_file}")
        console.print(f"[blue]Target table:[/blue] {table}")
        console.print(f"[blue]Mode:[/blue] replace (overwrite existing table)")
        
        # Use provided config or load default
        if config is None:
            config = Config()
        db_url = config.get_database_url()
        
        # Read XLSX file
        console.print(f"[yellow]Reading police data XLSX file (sheet: {sheet})...[/yellow]")
        try:
            # Handle sheet parameter (can be string name or integer index)
            sheet_name = sheet if isinstance(sheet, str) or sheet == 0 else int(sheet)
            df = pd.read_excel(xlsx_file, sheet_name=sheet_name)
            console.print(f"[green]✓[/green] Successfully read {len(df)} criminal records, {len(df.columns)} data fields")
        except Exception as e:
            console.print(f"[red]Error reading police XLSX file:[/red] {str(e)}")
            return

        # Clean up temporary file if it was downloaded, after successful read
        if temp_file_path:
            try:
                temp_file_path.unlink()
                # Also try to remove the temporary directory if it's empty
                try:
                    temp_file_path.parent.rmdir()
                except OSError:
                    # Directory not empty or other issues, ignore
                    pass
            except Exception:
                # Cleanup failed, but don't break the main process
                pass
        
        # Clean column names for Brazilian police data standards (remove spaces, special characters)
        df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]
        
        # Convert problematic data types for Brazilian police data compatibility with SQLite
        console.print(f"[yellow]Converting Brazilian police data types for SQLite compatibility...[/yellow]")
        for col in df.columns:
            # Convert datetime.time to string
            if df[col].dtype == 'object':
                # Check if column contains time objects
                sample_values = df[col].dropna().head(10)
                if len(sample_values) > 0 and any(hasattr(val, 'hour') and hasattr(val, 'minute') for val in sample_values):
                    df[col] = df[col].astype(str)
                    console.print(f"[blue]Converted time column '{col}' to string[/blue]")
            
            # Convert other datetime types to string if needed
            elif 'datetime' in str(df[col].dtype).lower() and 'datetime64' not in str(df[col].dtype):
                df[col] = df[col].astype(str)
                console.print(f"[blue]Converted datetime column '{col}' to string[/blue]")
        
        # Add auto-incremental ID column to preserve entry order
        console.print(f"[yellow]Adding auto-incremental ID column for entry order tracking...[/yellow]")
        df.reset_index(drop=True, inplace=True)  # Ensure clean index
        df.insert(0, 'ordem_insercao', range(1, len(df) + 1))  # Add 1-based ID column as first column
        console.print(f"[green]✓[/green] Added 'ordem_insercao' column with {len(df)} sequential IDs")

        # Display data preview
        _display_data_preview(df)
        
        # Connect to database
        engine = create_engine(db_url)
        
        # In replace mode, we don't need to validate existing table compatibility
        console.print(f"[green]✓[/green] Using replace mode - table will be created/replaced")
        
        if dry_run:
            console.print(f"[yellow]Dry run mode - no data would be inserted[/yellow]")
            console.print(f"[blue]Would create/update table '{table}' with {len(df)} rows[/blue]")
            return
        
        # Insert criminal data into database
        console.print(f"[yellow]Inserting Brazilian criminal data into {table} (replace mode)...[/yellow]")
        try:
            # For large datasets, use chunked insertion to avoid "too many SQL variables" error
            chunk_size = 1000  # SQLite default limit is around 999 variables
            total_rows = len(df)

            def _insert_chunk(chunk_df: pd.DataFrame, if_exists: str) -> None:
                """Insert a chunk of data into the database table."""
                chunk_df.to_sql(
                    name=table,
                    con=engine,
                    if_exists=if_exists,
                    index=False,
                    method=None  # Use default method for better compatibility
                )

            if total_rows > chunk_size:
                console.print(f"[blue]Large dataset detected ({total_rows} rows) - using chunked insertion[/blue]")
                
                # First chunk with replace to create/replace table
                first_chunk = df.iloc[:chunk_size]
                _insert_chunk(first_chunk, "replace")
                
                # Remaining chunks with append
                for i in range(chunk_size, total_rows, chunk_size):
                    chunk = df.iloc[i:i + chunk_size]
                    _insert_chunk(chunk, "append")
                    console.print(f"[blue]Progress:[/blue] {min(i + chunk_size, total_rows)}/{total_rows} criminal records inserted")
            else:
                # Small dataset - use single insertion
                _insert_chunk(df, "replace")

            console.print(f"[green]✓[/green] Successfully inserted {len(df)} criminal records into {table}")
            
        except SQLAlchemyError as e:
            # Handle SQLAlchemy errors more gracefully
            error_msg = str(e)
            
            # Truncate very long error messages
            if len(error_msg) > ERROR_MSG_TRUNCATE_LENGTH:
                error_msg = error_msg[:ERROR_MSG_TRUNCATE_LENGTH] + "... (truncated)"
            
            # Extract key information from common SQLAlchemy errors
            if "too many SQL variables" in error_msg.lower():
                console.print(f"[red]Error:[/red] Too many columns/rows for single insertion")
                console.print(f"[yellow]Suggestion:[/yellow] Try reducing the dataset size or contact support")
            elif "type 'datetime.time' is not supported" in error_msg.lower():
                console.print(f"[red]Error:[/red] Time data type not supported by SQLite")
                console.print(f"[yellow]Suggestion:[/yellow] Time columns should be converted to strings")
            elif "UNIQUE constraint failed" in error_msg:
                console.print(f"[red]Error:[/red] Unique constraint violation - duplicate data detected")
            elif "no such table" in error_msg.lower():
                console.print(f"[red]Error:[/red] Table '{table}' does not exist")
            elif "database is locked" in error_msg.lower():
                console.print(f"[red]Error:[/red] Database is locked - please close other connections")
            elif "datatype mismatch" in error_msg.lower():
                console.print(f"[red]Error:[/red] Data type mismatch between XLSX and table schema")
            else:
                console.print(f"[red]Database Error:[/red] {error_msg}")
            
            return
        except Exception as e:
            console.print(f"[red]Error inserting data:[/red] {str(e)}")
            return
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")


def _download_xlsx_file(url: str) -> Path:
    """Download XLSX file from URL to temporary location.
    
    Returns:
        Path: The temporary file path that needs cleanup after use
    """
    try:
        # Create a temporary file
        temp_dir = Path(tempfile.mkdtemp())
        filename = Path(urlparse(url).path).name
        if not filename.endswith('.xlsx'):
            filename += '.xlsx'
        temp_file = temp_dir / filename
        
        # Download the file
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(temp_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        console.print(f"[green]✓[/green] Downloaded {temp_file.stat().st_size} bytes")
        return temp_file  # Return the temporary file path for use and cleanup
        
    except requests.RequestException as e:
        console.print(f"[red]Error downloading file:[/red] {str(e)}")
        raise
    except Exception as e:
        console.print(f"[red]Error saving file:[/red] {str(e)}")
        raise


def _display_data_preview(df: pd.DataFrame) -> None:
    """Display a preview of the Brazilian police criminal data."""
    console.print("\n[blue]Criminal Data Preview:[/blue]")
    
    # Column information table
    col_table = Table(title="Police Data Column Information")
    col_table.add_column("Field", style="cyan")
    col_table.add_column("Type", style="green")
    col_table.add_column("Records Count", style="yellow")
    col_table.add_column("Sample Values", style="blue")
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        non_null_count = df[col].count()
        
        # Get sample non-null values
        sample_values = df[col].dropna().head(3).astype(str).tolist()
        sample_str = ", ".join(sample_values) if sample_values else "No data"
        if len(sample_str) > 30:
            sample_str = sample_str[:27] + "..."
        
        col_table.add_row(col, dtype, str(non_null_count), sample_str)
    
    console.print(col_table)
    
    # Criminal data shape summary
    console.print(f"\n[blue]Criminal Data Shape:[/blue] {df.shape[0]} police records × {df.shape[1]} data fields")


