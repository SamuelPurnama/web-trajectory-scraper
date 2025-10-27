# Deterministic Agent

Web navigation agent that follows predefined URL paths to generate verifiable trajectories.

## Features

- **Deterministic**: Follows exact URL paths with consistent behavior
- **Multi-strategy**: Handles clicking, scrolling, and hover interactions (sometimes)
- **Diverse**: Collectes data in different viewport configs

This agent does not use BrowserGym!


## Installation

```bash
source .venv/bin/activate
export BROWSERBASE_API_KEY="your_api_key"
export BROWSERBASE_PROJECT_ID="your_project_id"
uv run playwright install && uv run playwright install-deps
```

## Usage

### Generate Trajectories
```bash
uv run -m det_agent_generate_traj \
  --tasks_json extracted_paths/website_all_paths.json \
  --output_dir trajectories/ \
  --num_jobs 4 \
  --job_id 0 \
  --num_workers 2
```

### Parameters
- `tasks_json`: Path extraction output from website_graph
- `output_dir`: Directory for trajectory outputs
- `num_jobs`: Total parallel jobs
- `num_workers`: Workers per job
- `debug`: Enable debug mode

## Output Structure

```
trajectories/
├── task_website_0/
│   ├── axtree/
│   ├── expanded_axtrees/
│   ├── extra_element_properties/
│   ├── images/
│   ├── metadata.json
│   ├── system_message.md
│   ├── trajectory.html
│   ├── trajectory.json
│   ├── urls/
│   ├── user_message/
│   └── verdict.json
```
