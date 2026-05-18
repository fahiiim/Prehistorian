import typer
import sys
import os
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel

from .git_parser import parse_git_history, get_latest_commit_hash, get_staged_files, normalize_path
from .math_engine import train_model, save_model, load_model

if sys.platform == "win32":
    if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

app = typer.Typer(name="prehistorian", help="Predictive codebase cartographer.")
console = Console()

@app.command()
def scan():
    """Triggers the data pipeline and builds the co-change model."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        task1 = progress.add_task("[cyan]Parsing Git history...", total=None)
        
        commits = parse_git_history()
        latest_hash = get_latest_commit_hash()
        progress.update(task1, description="[cyan]Parsing completed.")
        
        task2 = progress.add_task("[magenta]Running Math Engine...", total=None)
        model = train_model(commits, latest_hash)
        
        save_model(model)
        
        progress.update(task2, description="[green]Model saved to .prehistorian/model.joblib")
        
        total_commits = len(commits)
        total_dependencies = sum(len(rules) for rules in model.co_change_probabilities.values())
        
        console.print(f"\n[bold green]Prehistorian analyzed {total_commits} commits. Found {total_dependencies} behavioral dependencies. Model saved.[/bold green]")

@app.command()
def query(file_path: str):
    """Finds files that historically co-change with the queried file."""
    model = load_model()
    if not model:
        console.print("[bold red]Model not found. Run `prehistorian scan` first.[/bold red]")
        raise typer.Exit(code=1)

    normalized_path = normalize_path(file_path)
    if normalized_path not in model.co_change_probabilities:
        console.print(f"[yellow]No historical co-change data found for {normalized_path}.[/yellow]")
        return

    rules = model.co_change_probabilities[normalized_path][:5]

    table = Table(title=f"Co-change Dependencies for '{normalized_path}'")
    table.add_column("File Path", style="cyan", no_wrap=True)
    table.add_column("Co-change Confidence (%)", justify="right", style="magenta")
    
    for rule in rules:
        table.add_row(rule.file_b, f"{rule.confidence:.2f}%")
        
    console.print(table)

@app.command(name="hook-install")
def hook_install():
    """Creates a git pre-commit hook targeting prehistorian pre-commit-check."""
    hook_path = ".git/hooks/pre-commit"
    
    if not os.path.exists(".git"):
        console.print("[bold red]Error: No .git directory found. Are you in the repo root?[/bold red]")
        raise typer.Exit(code=1)
        
    # Standard shell script
    hook_script = "#!/bin/sh\nprehistorian pre-commit-check\n"
    
    try:
        with open(hook_path, "w") as f:
            f.write(hook_script)
        # Assuming posix or git-bash like environment
        os.chmod(hook_path, 0o755)
        console.print(f"[bold green]Successfully installed pre-commit hook at {hook_path}[/bold green]")
    except Exception as e:
        console.print(f"[bold red]Failed to write pre-commit hook: {e}[/bold red]")
        raise typer.Exit(code=1)

@app.command(name="pre-commit-check")
def pre_commit_check():
    """Runs automatically during git commit to warn about missing co-changed files."""
    model = load_model()
    if not model:
        # Ignore if model isn't built. Don't block commits.
        sys.exit(0)
        
    staged_files = set(get_staged_files())
    if not staged_files:
        sys.exit(0)
        
    for staged_file in staged_files:
        if staged_file in model.co_change_probabilities:
            # Check top 2 rules
            top_rules = model.co_change_probabilities[staged_file][:2]
            for rule in top_rules:
                if rule.confidence >= 75.0 and rule.file_b not in staged_files:
                    # Warn the user
                    warning_text = (
                        f"[bold yellow][PREHISTORIAN WARNING][/bold yellow] You are committing "
                        f"'{staged_file}', but historically you also change '{rule.file_b}' "
                        f"{rule.confidence:.0f}% of the time. Did you forget to stage it?"
                    )
                    panel = Panel(warning_text, expand=False, border_style="yellow")
                    console.print(panel)
                    
    # ALWAYS EXIT 0 (Never block git commit)
    sys.exit(0)

if __name__ == "__main__":
    app()
