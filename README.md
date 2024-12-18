# MdXLogseqTODOSync

A Python tool to synchronize TODO items between Markdown and Logseq files. It allows you to maintain TODO lists across different markdown formats while respecting delimiters and filtering based on patterns and bullet point levels.

I made this so that updating my [logseq](https://github.com/logseq/logseq) graph's TODOs about a given repository would update the README.md of said repository.

## Features

- Synchronize TODO items between different markdown files
- Configurable delimiters to mark sync boundaries
- Filter content based on regular expression patterns
- Control maximum bullet point depth
- Preserves formatting and indentation
- Type-safe implementation with beartype

## Getting started
* From pypi:
    * As a tool: `uvx MdXLogseqTODOSync@latest --help`
    * Via uv: `uv pip install MdXLogseqTODOSync`
    * Via pip: `pip install MdXLogseqTODOSync`
* From github:
    * Clone this repo then `pip install .`

## Usage

The tool is primarily used from the command line:

```bash
MdXLogseqTODOSync --help

# Basic usage
MdXLogseqTODOSync input.md output.md

# With filtering options
MdXLogseqTODOSync --must_match_regex "TODO|DONE" --bulletpoint-max-level 2 input.md output.md

# Full options
MdXLogseqTODOSync \
    --input-delim-start "- BEGIN_TODO" \
    --input-delim-end "- END_TODO" \
    --output-delim-start "<!-- BEGIN_TODO -->" \
    --output-delim-end "<!-- END_TODO -->" \
    --must_match_regex "TODO|DONE" \
    --bulletpoint-max-level 2 \
    --sub-pattern '(\s*)- (TODO|DONE|DOING|NOW|LATER) ' '\\1- ' \
    --remove-block-properties \
    --keep-new-lines \
    --recursive \
    input.md output.md
```

### Configuration Options

- `input_file`: Path or string pointing to the input Markdown/Logseq file
- `output_file`: Path or string pointing to the output Markdown/Logseq file
- `input_delim_start`: Regex pattern to match the start of input section. Use "__START__" for beginning of file. Default: `"__START__"`
- `input_delim_end`: Regex pattern to match the end of input section. Use "__END__" for end of file. Default: `"__END__"`
- `output_delim_start`: Regex pattern to match the start of output section. Default: `"<!-- BEGIN_TODO -->"`
- `output_delim_end`: Regex pattern to match the end of output section. Default: `"<!-- END_TODO -->"`
- `bulletpoint_max_level`: Maximum level of bullet points to process. Use -1 for unlimited. Default: `-1`
- `must_match_regex`: Regex pattern that lines must match to be included. Default: `r"^\s*- (TODO|DONE|DOING|NOW|LATER|#+) "`
- `sub_pattern`: Optional tuple of (search pattern, replace pattern) to modify matched lines. Default: `(r"^(\s*)- (TODO|DONE|DOING|NOW|LATER) ", r"\1- ")`
- `remove_block_properties`: If True, removes Logseq block properties. Default: `True`
- `keep_new_lines`: If True, preserves newlines from Logseq. Default: `True`
- `recursive`: If True, processes nested TODO items under a matching parent. Default: `True`

### File Format

Input file example:
```markdown
Some content...

- BEGIN_TODO
- TODO Review pull request
  - DONE Update tests
  - TODO Add documentation
- END_TODO

More content...
```

Output file example:
```markdown
# Project TODOs

<!-- BEGIN_TODO -->
- TODO Review pull request
  - DONE Update tests
  - TODO Add documentation
<!-- END_TODO -->
```

## Error Handling

The tool includes robust error checking for:
- Missing or duplicate delimiters
- Non-existent input files
- Empty or invalid content blocks
- Invalid regex patterns

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See LICENSE.md file for details.
