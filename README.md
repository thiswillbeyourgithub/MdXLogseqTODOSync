# MdXLogseqTODOSync

A Python tool to synchronize TODO items between Markdown and Logseq files. It allows you to maintain TODO lists across different markdown formats while respecting delimiters and filtering based on patterns and bullet point levels.

## Features

- Synchronize TODO items between different markdown files
- Configurable delimiters to mark sync boundaries
- Filter content based on regular expression patterns
- Control maximum bullet point depth
- Preserves formatting and indentation
- Type-safe implementation with beartype

## Getting started
* From pypi:
    * As a tool: `uvx MdXLogseqTODOSync@latest --help`  # TODO: can this be used as a tool?
    * Via uv: `uv pip install MdXLogseqTODOSync`
    * Via pip: `pip install MdXLogseqTODOSync`
* From github:
* Clone this repo then `pip install .`

## Usage

The tool is primarily used from the command line:

```bash
mdxlogseqtodosync --help

# Basic usage
mdxlogseqtodosync input.md output.md

# With filtering options
mdxlogseqtodosync --pattern "TODO|DONE" --max-level 2 input.md output.md

# Full options
mdxlogseqtodosync \
    --input-start "- BEGIN_TODO" \
    --input-end "- END_TODO" \
    --output-start "<!-- BEGIN_TODO -->" \
    --output-end "<!-- END_TODO -->" \
    --pattern "TODO|DONE" \
    --max-level 2 \
    input.md output.md
```

### Configuration Options

- `input_file`: Source markdown file path
- `output_file`: Destination markdown file path
- `input_delim_start`: Start delimiter pattern for input file (default: `"- BEGIN_TODO"`)
- `input_delim_end`: End delimiter pattern for input file (default: `"- END_TODO"`)
- `output_delim_start`: Start delimiter for output file (default: `"<!-- BEGIN_TODO -->"`)
- `output_delim_end`: End delimiter for output file (default: `"<!-- END_TODO -->"`)
- `bulletpoint_max_level`: Maximum bullet point level to process (-1 for unlimited)
- `required_pattern`: Regex pattern that lines must match to be included. Default is `r"\s*- (TODO|DONE)"`

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
