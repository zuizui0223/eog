"""CLI wrapper for the packaged A-Islands species screen."""

from eog.aislands_species_screen import main, summarize_species

__all__ = ["main", "summarize_species"]


if __name__ == "__main__":
    main()
