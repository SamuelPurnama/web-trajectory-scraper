# Website Explorer

A tool for systematically exploring websites to collect interesting navigation paths for agent training data.

## Features

- **Scalable**: Add domains to collect more data
- **Verifiable**: Known paths from systematic exploration
- **Diverse**: Covers different pages and functionality

## Installation

```bash
uv pip install pyvis
uv run playwright install && uv run playwright install-deps
```

## Usage

### Single Website
```bash
uv run --active -m website_explorer https://autozone.com --max-depth 2 --depth-max-items "10,3" --output-dir test_autozone
```

### Batch Processing (recommended)
Edit configs in `parallel_batch_explorer`:
```bash
uv run -m parallel_batch_explorer
```

After graphs are made we need to extract individual paths and turn them into tasks.
This command will create the tasks(jsons) :

```bash
uv run -m path_extractor /path/to/batch_directory
```

## Process

1. **Load homepage**: Extract all links with contextual information:
   ```
   [372] listitem '', visible
       [373] link 'Topics', clickable, visible, url='https://github.com/topics'
   [374] listitem '', visible
       [375] link 'Trending', clickable, visible, url='https://github.com/trending'
   [376] listitem '', visible
       [377] link 'Collections', clickable, visible, url='https://github.com/collections'
   ```

2. **LLM link selection**: An LLM picks interesting, functional, and navigational links

3. **Breadth-first exploration**: Continue the process on selected links until the website is covered

## Output Structure

```
output_dir/
├── axtree_json/
├── blacklists/
├── cars_com_website_graph_1752640115.html
├── cars_com_website_graph_1752640115.json
├── cars_com_website_graph_1752640115_blacklist.txt
├── cars_com_website_graph_1752640115_visited.txt
├── html/
├── llm_input/
├── llm_output/
└── screenshots/
```

## Path Format

```json
{
  "path": [
    "https://www.coursera.org/",
    "https://www.coursera.org/degrees", 
    "https://www.coursera.org/career-academy?trk_ref=globalnav",
    "https://www.coursera.org/articles/what-is-project-manager"
  ],
  "length": 4,
  "name": "coursera"
}
```

These can be later fed into the deterministic agent to produce verifiable navigation trajectories. Example website:

![Example Graph](example_graph.png)

