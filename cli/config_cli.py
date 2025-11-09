import typer
from core.config import ConfigManager

app = typer.Typer(help="Manage QueueCTL configuration settings")

config = ConfigManager()

# ----------------------------------------------------------------------
# SET
# ----------------------------------------------------------------------
@app.command("set")
def set(key: str, value: str):
    """Set a configuration key-value pair."""
    try:
        if value.isdigit():
            value = int(value)
        elif value.lower() in ["true", "false"]:
            value = value.lower() == "true"

        config.set(key, value)
        typer.echo(f"Configuration updated: {key} = {value}")
    except Exception as e:
        typer.echo(f"Error updating configuration: {e}")
        raise typer.Exit(code=1)

# ----------------------------------------------------------------------
# GET
# ----------------------------------------------------------------------
@app.command("get")
def get(key: str):
    """Retrieve a specific configuration value."""
    try:
        value = config.get(key)
        if value is None:
            typer.echo(f"No configuration key found for '{key}'")
        else:
            typer.echo(f"{key} = {value}")
    except Exception as e:
        typer.echo(f"Error reading configuration: {e}")
        raise typer.Exit(code=1)

# ----------------------------------------------------------------------
# SHOW
# ----------------------------------------------------------------------
@app.command("show")
def show():
    """Display all current configuration settings."""
    try:
        cfg = config.load()
        typer.echo("\nQueueCTL Configuration")
        typer.echo("-" * 40)
        for k, v in cfg.items():
            typer.echo(f"{k:<15}: {v}")
    except Exception as e:
        typer.echo(f"Error loading configuration: {e}")
        raise typer.Exit(code=1)

# ----------------------------------------------------------------------
# RESET
# ----------------------------------------------------------------------
@app.command("reset")
def reset():
    """Reset configuration to default values."""
    try:
        config.reset()
        typer.echo("Configuration reset to default values.")
    except Exception as e:
        typer.echo(f"Error resetting configuration: {e}")
        raise typer.Exit(code=1)
