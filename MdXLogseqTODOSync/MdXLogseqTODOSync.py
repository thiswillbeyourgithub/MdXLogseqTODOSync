from beartype import beartype
from pathlib import Path
from collections.abc import Sequence
import LogseqMarkdownParser
import re

@beartype  # this will apply to all methods
class MdXLogseqTODOSync:
    VERSION: str = "0.0.1"

    def __init__(
        self,
        input_file: Path | str,
        output_file: Path | str,
        input_delims: Sequence[str] = (r"<!-- BEGIN_TODO -->", r"<!-- END_TODO -->"),
        output_delims: Sequence[str] = (r"- BEGIN_TODO", r"- END_TODO"),
        bulletpoint_max_level: int = -1,
        required_pattern: str = r".*",
        ) -> None:

        """
        Initialize the MdXLogseqTODOSync class.

        Args:
            input_file: Path or string pointing to the input file
            output_file: Path or string pointing to the output file
            input_delims: Tuple of (start, end) regex patterns to match input file delimiters
            output_delims: Tuple of (start, end) regex patterns to match output file delimiters
            bulletpoint_max_level: Maximum level of bullet points to process (-1 for unlimited)
            required_pattern: Regex pattern that lines must match to be included
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.input_delims = input_delims
        self.output_delims = output_delims
        self.bulletpoint_max_level = bulletpoint_max_level
        self.required_pattern = required_pattern

    def process_input(self) -> list[str]:
        """
        Process the input file using LogseqMarkdownParser.
        
        Returns:
            List of processed lines that match the required pattern
        """
        with open(self.input_file, 'r') as f:
            content = f.read()
            
        # Parse the content using LogseqMarkdownParser
        page = LogseqMarkdownParser.parse_text(content=content, verbose=False)
        
        # Process blocks and filter based on required_pattern
        matched_lines = []
        pattern = re.compile(self.required_pattern)
        
        for block in page.blocks:
            # Get the block content and check against pattern
            block_content = block.dict().get('content', '')
            if pattern.search(block_content):
                # Calculate indentation based on block level
                level = block.dict().get('level', 0)
                
                # If bulletpoint_max_level is set, skip blocks that are too deep
                if self.bulletpoint_max_level != -1 and level > self.bulletpoint_max_level:
                    continue
                    
                # Add appropriate number of spaces for indentation
                indentation = '  ' * level
                matched_lines.append(f"{indentation}- {block_content}")
        
        return matched_lines
