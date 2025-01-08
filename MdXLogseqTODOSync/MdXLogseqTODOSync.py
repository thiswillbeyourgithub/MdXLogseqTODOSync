from textwrap import dedent
from beartype import beartype
from pathlib import Path
from collections.abc import Sequence
import LogseqMarkdownParser
import re
import typing

@beartype  # this will apply to all methods
class MdXLogseqTODOSync:
    VERSION: str = "0.0.19"

    def __init__(
        self,
        input_file: Path | str,
        output_file: Path | str,

        input_delim_start: str = r"__START__",
        input_delim_end: str = r"__END__",

        output_delim_start: str = r"<!-- BEGIN_TODO -->",
        output_delim_end: str = r"<!-- END_TODO -->",

        bulletpoint_max_level: int = -1,
        must_match_regex: str = r"^\s*- (TODO|DONE|DOING|NOW|LATER|#+) ",
        sub_pattern: typing.Optional[typing.Tuple[str, str]] = (r"^(\s*)- (TODO|DONE|DOING|NOW|LATER) ", r"\1- "),
        remove_block_properties: bool = True,
        keep_new_lines: bool = True,
        recursive: bool = True,
        ) -> None:
        """
        Initialize the MdXLogseqTODOSync class.

        This class synchronizes TODO items between Markdown and Logseq files, respecting
        delimiter boundaries and filtering based on patterns and bullet point levels.
        It reads from an input file, processes the content between specified delimiters,
        and writes the filtered content to an output file.

        Args:
            input_file (Path | str): Path or string pointing to the input Markdown/Logseq file.
            output_file (Path | str): Path or string pointing to the output Markdown/Logseq file.
            input_delim_start (str, optional): Regex pattern to match the start of input section. Use "__START__" for beginning of file. Default: "__START__".
            input_delim_end (str, optional): Regex pattern to match the end of input section. Use "__END__" for end of file. Default: "__END__".
            output_delim_start (str, optional): Regex pattern to match the start of output section. Default: "<!-- BEGIN_TODO -->".
            output_delim_end (str, optional): Regex pattern to match the end of output section. Default: "<!-- END_TODO -->".
            bulletpoint_max_level (int, optional): Maximum level of bullet points to process. Use -1 for unlimited. Default: -1.
            must_match_regex (str, optional): Regex pattern that lines must match to be included. Default: r"^\s*- (TODO|DONE|DOING|NOW|LATER|#+) ".
            sub_pattern (tuple[str, str] | None, optional): Optional tuple of (search pattern, replace pattern) to modify matched lines. Only the first pattern will be compiled. Default: (r"^(\s*)- (TODO|DONE|DOING|NOW|LATER) ", r"\1- ").
            remove_block_properties (bool, optional): If True, removes Logseq block properties. Default: True.
            keep_new_lines (bool, optional): If True, preserves newlines from Logseq. Default: True.
            recursive (bool, optional): If True, processes nested TODO items under a matching parent. Default: True.

        Raises:
            ValueError: If delimiters are missing or appear multiple times in files.
            FileNotFoundError: If input file doesn't exist.
            AssertionError: If no blocks or matching lines are found in input.
            Exception: If there's an error compiling the sub_pattern or must_match_regex.
        """
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.input_delims = [input_delim_start, input_delim_end]
        self.output_delims = [output_delim_start, output_delim_end]
        self.bulletpoint_max_level = bulletpoint_max_level
        self.must_match_regex = must_match_regex
        self.sub_pattern = sub_pattern
        if sub_pattern:
            try:
                self.sub_pattern = re.compile(sub_pattern[0]), sub_pattern[1]
            except Exception as e:
                raise Exception(f"Error when compiling sub_pattern's arguments: '{e}'") from e
        self.remove_block_properties = remove_block_properties
        self.keep_new_lines = keep_new_lines
        self.recursive = True

        matched_lines = self.process_input()
        assert matched_lines, "No matching lines found in input"
        self.process_output(matched_lines)
        return

    def _validate_delimiters(self, content: str, delims: Sequence[str], file_type: str) -> None:
        """
        Validate that delimiters appear exactly once in the content.

        This method ensures the integrity of sync boundaries by checking that both start
        and end delimiters appear exactly once in the given content.

        Args:
            content (str): The file content to check.
            delims (Sequence[str]): Tuple or list of (start, end) delimiters to check.
            file_type (str): String indicating which file is being checked ('input' or 'output').

        Raises:
            ValueError: If any delimiter is missing or appears multiple times. The error
                        message will specify which delimiter caused the issue.

        Note:
            The start delimiter "__START__" is a special case that doesn't need to be present in the content.
            The end delimiter "__END__" is a special case that allows processing until the end of the file.
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

        This method reads the input file, validates delimiters, and processes blocks between
        the specified input delimiters. It filters blocks based on the required pattern and
        maximum bullet point level.

        Returns:
            list[str]: Processed and filtered lines with proper indentation.

        Raises:
            ValueError: If input delimiters are missing or appear multiple times.
            FileNotFoundError: If the input file doesn't exist.
            AssertionError: If no blocks or matching lines are found in the input.
            Exception: If there's an error compiling the must_match_regex.

        Note:
            - The special start delimiter "__START__" indicates processing from the beginning of the file.
            - The special end delimiter "__END__" indicates processing until the end of the file.
            - If recursive processing is enabled, it will include nested items under a matching parent.
            - Block properties and LOGBOOK entries can be removed based on the remove_block_properties setting.
        """
        assert self.input_file.exists() and self.input_file.is_file(), f"File '{self.input_file}' not found or not a file"
        with open(self.input_file, 'r') as f:
            content = f.read()

        self._validate_delimiters(content, self.input_delims, 'input')

        # Parse the content using LogseqMarkdownParser
        page = LogseqMarkdownParser.parse_text(content=content, verbose=False)

        # First collect all matching blocks
        matching_blocks = []
        try:
            pattern = re.compile(self.must_match_regex)
        except Exception as e:
            raise Exception(f"Error when compiling must_match_regex argument: '{e}'") from e
        start_delim, end_delim = self.input_delims

        # Track if we're inside the delimited section
        inside_section = False

        assert page.blocks, "No blocks found in input"

        previous_indentation = page.blocks[0].indentation_level
        for block in page.blocks:
            block_content = block.content

            if block.indentation_level < previous_indentation:
                previous_indentation = block.indentation_level

            # Check for delimiter markers
            if start_delim == "__START__":
                inside_section = True
                start_delim = "a"
                while start_delim in content:
                    start_delim *= 2
            elif re.findall(start_delim, block_content):
                inside_section = True
                continue
            elif inside_section and end_delim != "__END__" and re.findall(end_delim, block_content):
                break  # Stop processing after end delimiter

            if inside_section and (pattern.search(block_content) or (self.recursive and block.indentation_level > previous_indentation)):
                # Store blocks that match the pattern
                matching_blocks.append(block)
                previous_indentation = block.indentation_level

        assert matching_blocks, "No blocks found in input"

        # Process the matching blocks
        matched_lines = []
        previous_indentation = matching_blocks[0].indentation_level
        for block in matching_blocks:
            if block.indentation_level < previous_indentation:
                previous_indentation = block.indentation_level

            # If bulletpoint_max_level is set, skip blocks that are too deep
            if (
                    self.bulletpoint_max_level == -1 or
                    block.indentation_level >= self.bulletpoint_max_level or
                    (self.recursive and block.indentation_level > previous_indentation)
            ):
                previous_indentation = block.indentation_level
                if self.remove_block_properties:
                    keys = block.properties.keys()
                    for k in keys:
                        block.del_property(k)
                    if ":LOGBOOK:" in block.content and ":END:" in block.content:
                        content = re.sub(":LOGBOOK:.*:END:", "", block.content, flags=re.MULTILINE|re.DOTALL).rstrip()
                        matched_lines.append(content)
                    else:
                        matched_lines.append(block.content)
                else:
                    matched_lines.append(block.content)

        return matched_lines

    def process_output(self, matched_lines: list[str]) -> None:
        """
        Process the output file by replacing content between delimiters with matched lines.

        This method handles the output file operations:
        - If the output file exists, it replaces content between output delimiters with new matched lines.
        - If the file doesn't exist or doesn't contain delimiters, it creates a new file or appends content.
        - The content is properly dedented before insertion.

        Args:
            matched_lines (list[str]): List of processed lines to insert between delimiters.

        Raises:
            ValueError: If output delimiters appear multiple times in the existing file.
            OSError: If unable to write to the output file.

        Note:
            - The method applies any substitution patterns specified in sub_pattern.
            - It respects the keep_new_lines setting when processing the matched lines.
            - The final content is written with spaces instead of tabs for consistency.
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
        filtered_lines = [m for m in matched_lines if (self.keep_new_lines or m.strip())]
        if self.sub_pattern:
            filtered_lines = [re.sub(self.sub_pattern[0], self.sub_pattern[1], line) for line in filtered_lines]
        replacement += dedent("\n".join(filtered_lines).replace("\t", "    "))
        replacement += f"\n{end_delim}"

        # Replace content between delimiters or append if not found
        if re.search(pattern, content, re.DOTALL):
            new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        else:
            new_content = content + "\n" + replacement if content else replacement

        # Write the modified content back to the file
        with open(self.output_file, 'w') as f:
            f.write(new_content)
