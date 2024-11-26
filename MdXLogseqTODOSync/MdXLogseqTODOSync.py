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
        Only processes blocks between input_delims markers.
        
        Returns:
            List of processed lines that match the required pattern
        """
        with open(self.input_file, 'r') as f:
            content = f.read()
            
        # Parse the content using LogseqMarkdownParser
        page = LogseqMarkdownParser.parse_text(content=content, verbose=False)
        
        # First collect all matching blocks
        matching_blocks = []
        pattern = re.compile(self.required_pattern)
        start_delim, end_delim = self.input_delims
        
        # Track if we're inside the delimited section
        inside_section = False
        
        for block in page.blocks:
            block_content = block.dict().get('content', '')
            
            # Check for delimiter markers
            if start_delim in block_content:
                inside_section = True
                continue
            elif end_delim in block_content:
                break  # Stop processing after end delimiter
                
            if inside_section and pattern.search(block_content):
                # Store blocks that match the pattern
                matching_blocks.append(block)
        
        # Process the matching blocks
        matched_lines = []
        for block in matching_blocks:
            level = block.indentation_level
            
            # If bulletpoint_max_level is set, skip blocks that are too deep
            if self.bulletpoint_max_level != -1 and level > self.bulletpoint_max_level:
                continue
                
            # Add appropriate number of spaces for indentation
            indentation = '  ' * level
            matched_lines.append(f"{indentation}- {block.dict().get('content', '')}")
        
        return matched_lines

    def process_output(self, matched_lines: list[str]) -> None:
        """
        Process the output file by replacing content between delimiters with matched lines.
        
        Args:
            matched_lines: List of processed lines to insert
        """
        # Read the output file content
        try:
            with open(self.output_file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""  # Start with empty content if file doesn't exist
            
        start_delim, end_delim = self.output_delims
        
        # Create the pattern to match everything between delimiters
        pattern = f"{start_delim}.*?{end_delim}"
        
        # Prepare the replacement content
        replacement = f"{start_delim}\n"
        replacement += "\n".join(matched_lines)
        replacement += f"\n{end_delim}"
        
        # Replace content between delimiters or append if not found
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            new_content = content + "\n" + replacement if content else replacement
            
        # Write the modified content back to the file
        with open(self.output_file, 'w') as f:
            f.write(new_content)
