# Website Task Generator

This module generates web task files for websites using ChatGPT via the `ell` library.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your ell library API key (follow ell library documentation)

## Usage

### Process all websites from CSV
```bash
python generate_website_tasks.py
```

### Process with custom parameters
```bash
python generate_website_tasks.py --start-index 0 --max-websites 10 --delay 2.0
```

### Process a single website
```bash
python generate_website_tasks.py --single-website "https://www.example.com"
```

### Custom file paths
```bash
python generate_website_tasks.py --csv-file custom_websites.csv --output-dir my_tasks --prompt-template my_prompt.txt
```

## Parameters

- `--csv-file`: Path to CSV file with websites (default: 585_websites.csv)
- `--output-dir`: Output directory for generated files (default: generated_tasks)
- `--prompt-template`: Path to prompt template file (default: prompt.txt)
- `--reference-file`: Path to reference file (default: reference_file.txt)
- `--axtree-file`: Path to axtree file (optional)
- `--start-index`: Index to start processing from (default: 0)
- `--max-websites`: Maximum number of websites to process
- `--single-website`: Process only a single website URL
- `--delay`: Delay between requests in seconds (default: 1.0)

## Output

Generated task files will be saved in the output directory with the naming convention:
`tasks_{domain}.py`

For example: `tasks_google_com.py`, `tasks_amazon_com.py`

## Logging

The module creates a log file `task_generation.log` with detailed information about the generation process.

## TODO List

- [ ] Add axtree data to the prompt template
- [ ] Automatically remove ```python ``` from generated .py files
- [ ] Make a default save directory for JSON task files
- [ ] Make a default save directory for generated Python files
- [ ] Add the default directory paths to the prompt template
- [ ] Create a bash script to chain the 4 commands (generate Python file, clean markdown, generate tasks, save JSON)
