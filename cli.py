from __future__ import annotations
import typer
from typing import Optional
from src import preprocess as prep
from src import train as tr
from src import evaluate as ev

app = typer.Typer(help="Cancer Detection project CLI")

@app.command()
def preprocess():
    """Preprocess raw images into processed directory."""
    prep.preprocess()

@app.command()
def train(epochs: Optional[int] = typer.Option(None, help="Override epochs")):
    if epochs is not None:
        from src.config.settings import settings as cfg
        cfg.epochs = epochs  # runtime override
    tr.main()

@app.command()
def evaluate():
    ev.main()

if __name__ == "__main__":
    app()
