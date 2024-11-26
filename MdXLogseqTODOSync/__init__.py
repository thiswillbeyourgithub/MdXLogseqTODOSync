
import sys
import fire

from .MdXLogseqTODOSync import MdXLogseqTODOSync

__all__ = ["MdXLogseqTODOSync"]

__VERSION__ = MdXLogseqTODOSync.VERSION

def cli_launcher() -> None:
    if sys.argv[-1] ==  "--version":
        return(f"MdXLogseqTODOSync version: {__VERSION__}")
    fire.Fire(MdXLogseqTODOSync)

if __name__ == "__main__":
    cli_launcher()