"""CLI interface for crawl_site."""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.traceback import install as install_traceback

from crawl_site.crawler import crawl_website, preview_crawl

app = typer.Typer(no_args_is_help=True)
console = Console()

# Install rich traceback handler
install_traceback(show_locals=True, console=console)


@app.command()
def crawl(
    url: str = typer.Argument(..., help="Starting URL to crawl"),
    max_pages: int = typer.Option(50, "--max-pages", "-n", help="Maximum pages to crawl"),
    output: str = typer.Option("./output", "--output", "-o", help="Output directory"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview URLs before crawling"),
):
    """Deep crawl a website and save each page as markdown.

    By default, only crawls pages under the starting URL's path.
    For example: https://example.com/docs/api will only crawl
    pages starting with https://example.com/docs/api
    """

    # Phase 1: Preview mode (if enabled)
    if preview:
        console.print(f"[bold]Discovering URLs from:[/bold] {url}")
        console.print()

        with console.status("[bold blue]Discovering URLs...", spinner="dots"):
            discovered_urls = asyncio.run(preview_crawl(url=url, max_pages=max_pages))

        if not discovered_urls:
            console.print("[red]No URLs discovered[/red]")
            raise typer.Exit(code=1)

        console.print(f"\n[bold green]Found {len(discovered_urls)} pages:[/bold green]\n")

        # Show ALL discovered URLs
        for i, discovered_url in enumerate(discovered_urls, 1):
            console.print(f"  {i}. {discovered_url}")

        console.print()

        # Update max_pages to actual discovered count
        actual_count = len(discovered_urls)
        if actual_count != max_pages:
            console.print(f"[yellow]Note: Discovered {actual_count} pages (max_pages was {max_pages})[/yellow]")
            max_pages = actual_count

        proceed = typer.confirm(
            f"Do you want to crawl all {actual_count} pages?",
            default=True,
        )

        if not proceed:
            console.print("[yellow]Crawl cancelled[/yellow]")
            raise typer.Exit(code=0)

        console.print()

    # Phase 2: Full crawl
    console.print(f"[bold]Crawling:[/bold] {url}")
    console.print(f"[bold]Max pages:[/bold] {max_pages}")
    console.print(f"[bold]Output:[/bold] {output}")
    console.print()

    # Create progress bar with custom URL field
    progress = Progress(
        TextColumn("[bold blue]{task.fields[current_url]}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TextColumn("{task.completed}/{task.total} pages"),
        TimeRemainingColumn(),
        console=console,
    )

    # Callback to update progress
    def on_page(page_url: str, success: bool):
        progress.update(task_id, advance=1, current_url=page_url)
        if success:
            progress.console.log(f"[green]✓[/green] {page_url}")

    # Run the crawl
    with progress:
        task_id = progress.add_task(
            "crawling",
            total=max_pages,
            current_url=url,
        )

        result = asyncio.run(
            crawl_website(
                url=url,
                max_pages=max_pages,
                output_dir=output,
                on_page_callback=on_page,
            )
        )

    # Display summary
    console.print()
    table = Table(title="Crawl Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")

    table.add_row("Total Pages", str(result.total_pages))
    table.add_row("Successful", str(result.successful_pages))
    table.add_row("Failed", str(result.failed_pages))
    table.add_row("Output Directory", str(Path(output).absolute()))

    console.print(table)
    console.print()

    # Show success/failure panel
    if result.successful_pages > 0:
        console.print(
            Panel(
                f"Successfully crawled {result.successful_pages} pages",
                title="Crawl Complete",
                style="green",
            )
        )
    else:
        console.print(
            Panel(
                "No pages were successfully crawled",
                title="Crawl Failed",
                style="red",
            )
        )
        raise typer.Exit(code=1)
