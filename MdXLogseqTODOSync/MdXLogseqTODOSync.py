from textwrap import dedent
from beartype import beartype
from pathlib import Path
from collections.abc import Sequence
import LogseqMarkdownParser
import re

@beartype  # this will apply to all methods
class MdXLogseqTODOSync:
    VERSION: str = "0.0.2"

    def __init__(
        self,
        input_file: Path | str,
        output_file: Path | str,

        input_delim_start: str = r"- BEGIN_TODO",
        input_delim_end: str = r"- END_TODO",

        output_delim_start: str = r"<!-- BEGIN_TODO -->",
        output_delim_end: str = r"<!-- END_TODO -->",

        bulletpoint_max_level: int = -1,
        required_pattern: str = r"\s*- (TODO|DONE)",
        ) -> None:

        """
        Initialize the MdXLogseqTODOSync class.

        This class synchronizes TODO items between Markdown and Logseq files, respecting
        delimiter boundaries and filtering based on patterns and bullet point levels.
        It reads from an input file, processes the content between specified delimiters,
        and writes the filtered content to an output file.

        Args:
            input_file: Path or string pointing to the input Markdown/Logseq file
            output_file: Path or string pointing to the output Markdown/Logseq file
            input_delim_start: Str regex pattern to match the start of input section (__START__ for BOF)
            input_delim_end: Str regex pattern to match the end of input section (__END__ for EOF)
            output_delim_start: Str regex pattern to match the start of output section
            output_delim_end: Str regex pattern to match the end of output section
            bulletpoint_max_level: Maximum level of bullet points to process (-1 for unlimited)
            required_pattern: Regex pattern that lines must match to be included. Default is `r"\s*- (TODO|DONE)"`

        Raises:
            ValueError: If delimiters are missing or appear multiple times in files
            FileNotFoundError: If input file doesn't exist
            AssertionError: If no blocks or matching lines are found in input
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.input_delims = [input_delim_start, input_delim_end]
        self.output_delims = [output_delim_start, output_delim_end]
        self.bulletpoint_max_level = bulletpoint_max_level
        self.required_pattern = required_pattern

        matched_lines = self.process_input()
        assert matched_lines, "No matching lines found in input"
        self.process_output(matched_lines)
        return

    def _validate_delimiters(self, content: str, delims: Sequence[str], file_type: str) -> None:
        """
        Validate that delimiters appear exactly once in the content.

        Checks both start and end delimiters to ensure they appear exactly once in the
        given content. This helps maintain the integrity of the sync boundaries.

        Args:
            content: The file content to check
            delims: Tuple of (start, end) delimiters to check
            file_type: String indicating which file is being checked ('input' or 'output')

        Raises:
            ValueError: If any delimiter is missing or appears multiple times, with a
                      descriptive message indicating which delimiter caused the error
        """
        start_delim, end_delim = delims

        # Check start delimiter
        if start_delim != "__START__":
            start_count = len(re.findall(start_delim, content))
            if start_count == 0:
                raise ValueError(f"Start delimiter not found in {file_type} file: {start_delim}")
            if start_count > 1:
                raise ValueError(f"Multiple start delimiters found in {file_type} file: {start_delim}")

        # Check end delimiter
        end_count = len(re.findall(end_delim, content))
        if end_count == 0 and end_delim != "__END__":
            raise ValueError(f"End delimiter not found in {file_type} file: {end_delim}")
        if end_count > 1:
            raise ValueError(f"Multiple end delimiters found in {file_type} file: {end_delim}")

    def process_input(self) -> list[str]:
        """
        Process the input file using LogseqMarkdownParser.

        Reads the input file, validates delimiters, and processes blocks between the specified
        input delimiters. Only blocks matching the required pattern and within the maximum
        bullet point level are included. The special end delimiter "__END__" can be used to
        process until the end of file.

        Returns:
            list[str]: Processed and filtered lines with proper indentation

        Raises:
            ValueError: If input delimiters are missing or appear multiple times
            FileNotFoundError: If input file doesn't exist
            AssertionError: If no blocks or matching lines are found in input
        """
        with open(self.input_file, 'r') as f:
            content = f.read()

        self._validate_delimiters(content, self.input_delims, 'input')

        # Parse the content using LogseqMarkdownParser
        page = LogseqMarkdownParser.parse_text(content=content, verbose=False)

        # First collect all matching blocks
        matching_blocks = []
        pattern = re.compile(self.required_pattern)
        start_delim, end_delim = self.input_delims

        # Track if we're inside the delimited section
        inside_section = False

        assert page.blocks, "No blocks found in input"

        for block in page.blocks:
            block_content = block.content

            # Check for delimiter markers
            if start_delim == "__START__":
                inside_section = True
            elif re.findall(start_delim, block_content):
                inside_section = True
                continue
            elif inside_section and end_delim != "__END__" and re.findall(end_delim, block_content):
                break  # Stop processing after end delimiter

            if inside_section and pattern.search(block_content):
                # Store blocks that match the pattern
                matching_blocks.append(block)

        assert matching_blocks, "No blocks found in input"

        # Process the matching blocks
        matched_lines = []

        # If bulletpoint_max_level is set, skip blocks that are too deep
        if self.bulletpoint_max_level != -1:
            for block in matching_blocks:
                if block.indentation_level >= self.bulletpoint_max_level:
                    matched_lines.append(block.content)
        else:
            matched_lines = [b.content for b in matching_blocks]

        return matched_lines

    def process_output(self, matched_lines: list[str]) -> None:
        """
        Process the output file by replacing content between delimiters with matched lines.

        If the output file exists, replaces content between output delimiters with the new
        matched lines. If the file doesn't exist or doesn't contain delimiters, creates
        a new file or appends content respectively. The content is properly dedented
        before insertion.

        Args:
            matched_lines: List of processed lines to insert between delimiters

        Raises:
            ValueError: If output delimiters appear multiple times in existing file
            OSError: If unable to write to output file
        """
        # Read the output file content
        try:
            with open(self.output_file, 'r') as f:
                content = f.read()
                # Only validate if file exists and has content
                if content:
                    self._validate_delimiters(content, self.output_delims, 'output')
        except FileNotFoundError:
            content = ""  # Start with empty content if file doesn't exist

        start_delim, end_delim = self.output_delims

        # Create the pattern to match everything between delimiters
        pattern = f"{start_delim}.*?{end_delim}"

        # Prepare the replacement content
        replacement = f"{start_delim}\n"
        replacement += dedent("\n".join(matched_lines))
        replacement += f"\n{end_delim}"

        # Replace content between delimiters or append if not found
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            new_content = content + "\n" + replacement if content else replacement

        # Write the modified content back to the file
        with open(self.output_file, 'w') as f:
            f.write(new_content)
