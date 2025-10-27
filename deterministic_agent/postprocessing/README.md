## Purpose

The data we collected needs to be further processed before training. This directory identifies the necessary steps and has individual modules to address each step. 


## Suggested workflow

1. Use the bash scripts to partition data:
   - `filter_success.sh` for fully completed (4 steps out of 4)
   - `filter_3_of_4.sh` for mostly completed (3 steps out of 4)
2. For ~12% of the data, the `trajectory.json` and `metadata.json` use outdated formats. Run `fix_legacy_jsons.py` on all trajectories to convert old formats.
3. To turn mostly complete trajectories into fully complete trajectories, run `trim_trajectories.py`. It trims 3/4 runs to clean 3/3. 
4. The tab switching action is incorrectly formatted for all trajectories. Apply correct tab switching with `remap_switch_tab.py`.
5. Run `add_open_page_title.py` to generate open page titles. This wasn't collected during data acquisition but is necessary for training. We use the HTML to retrieve this.
6. Generate high/mid/low LLM instructions with `generate_instruction.py`.
7. Update the format of the scroll action with `update_scroll_actions.py`.

## Details of each module

### `filter_success.sh`
Finds and copies fully successful trajectories (4/4) into a destination directory.

### `filter_3_of_4.sh`
Finds and copies trajectories that reached 3/4 steps (progress 0.67) into a destination directory.


### `fix_legacy_jsons.py`
Converts legacy `trajectory.json`/`metadata.json` to the modern schema, adds `viewport` from first screenshot, and renames 0-indexed assets to 1-indexed when needed.

Example:
from `trajectory.json` like this:
```json
[
  {
    "step": 0,
    "screenshot": "images/screenshot_000.png",
    "axtree": "axtree/axtree_000.txt",
    "global_axtree": "global_axtree/global_axtree_000.txt",
    "extra_element_properties": "extra_element_properties/extra_element_properties_000.json",
    "action": {
      "action": "goto",
      "url": "https://aternos.org"
    },
    "error": null,
    "timestamp": "2025-07-29T15:20:49.604403",
    "url": "https://www.wikipedia.org/"
  }
]
```

to:

```json
{
  "1": {
    "screenshot": "screenshot_001.png",
    "axtree": "axtree_001.txt",
    "user_message": "",
    "other_obs": {
      "page_index": 0,
      "url": "https://www.wikipedia.org/",
      "open_pages_titles": [
        "Wikipedia"
      ],
      "open_pages_urls": [
        "https://www.wikipedia.org/"
      ]
    },
    "action": {
      "action_str": "goto(url='https://aternos.org')",
      "action_description": "go to https://aternos.org",
      "action_output": {
        "thought": "",
        "action": {
          "url": "https://aternos.org"
        },
        "action_name": "goto"
      }
    },
    "error": null,
    "action_timestamp": 1753802449.604403
  }
}
```

for `metadata.json`:

from:
```json
{
  "path": [
    "https://aternos.org",
    "https://reddit.com/r/aternos",
    "https://reddit.com/r/admincraft/"
  ]
}
```

to:

```json
{
  "goal": "",
  "eps_name": "task_aternos_15948",
  "task": {
    "task_type": "",
    "keyword": "",
    "steps": [],
    "instruction": {
      "high_level": "",
      "mid_level": "",
      "low_level": ""
    }
  },
  "path": [
    "https://aternos.org",
    "https://reddit.com/r/aternos",
    "https://reddit.com/r/admincraft/"
  ],
  "viewport": {
    "width": 1280,
    "height": 720,
    "name": "Small Desktop Monitor"
  }
}
```

### `trim_trajectories.py`
Trims partial 3/4 trajectories to clean 3/3 by cutting at the correct step and appending an `exit` action; prunes files not referenced post-trim.

This adds a synthetic exit action at the last correct step.

### `remap_switch_tab.py`
Remaps `switch_tab` actions to `tab_focus` with correct `page_index`/`tab_id` increments and normalized action strings.

in `trajectory.json`
from:

```json
{
  "action": {
    "action": "switch_tab",
    "thought": "A new tab was opened, switching to it."
  }
}
```

to:

```json
{
  "action": {
    "action_str": "tab_focus(tab_id=1, page_index=1)",
    "action_description": "focus tab 1",
    "action_output": {
      "thought": "A new tab was opened, switching to it.",
      "action": {
        "tab_id": 1,
        "page_index": 1
      },
      "action_name": "tab_focus"
    }
  }
}
```


### `add_open_page_title.py`
Populates `other_obs.open_pages_titles` and `other_obs.open_pages_urls` per step by parsing HTML `<title>` and observed URLs; keeps `page_index` consistent across steps.

in `trajectory.json`

from:

```json
{
  "open_pages_titles": [],
  "open_pages_urls": []
}
```

to

```json
{
  "open_pages_titles": [
    "Wikipedia"
  ],
  "open_pages_urls": [
    "https://www.wikipedia.org/"
  ]
}
```

### `generate_instruction.py`
Generates high/mid/low instruction triplets from unique page URLs/screenshots using an LLM; writes `instruction_generation_output.json` and updates `metadata.json.task.instruction`.

Uses LLMs to write instructions after the trajectory is completed.

in `metadata.json`

from:

```json
{
  "instruction": {
    "high_level": "",
    "mid_level": "",
    "low_level": ""
  }
}
```

to:

```json
{
  "instruction": {
    "high_level": "Explore Aternos and Reddit to find discussions about player tracking and bans in Minecraft.",
    "mid_level": "Visit the Aternos website and then navigate to Reddit to find discussions related to Aternos, specifically focusing on player tracking and bans in Minecraft.",
    "low_level": "Start by visiting the Aternos homepage. Then, go to Reddit and search for the 'aternos' subreddit. Look for posts discussing player tracking and bans in Minecraft, and navigate to a relevant discussion thread."
  }
}
```


Also produces:
- `instruction_generation_input.html`
- `instruction_generation_output.json`

for debugging.


### `update_scroll_actions.py`

Updates how the scroll actions are written to make them compatible with training. delta_x is set to 0 and delta_y is 90% of the viewport height.

in 'trajectory.json' from:

```json
"action": {
  "action_str": "scroll(direction='down')",
  "action_description": "scroll on element with bid  in direction down",
  "action_output": {
    "thought": "",
    "action": {
      "direction": "down"
    },
    "action_name": "scroll"
  }
},
```

to:

```json
"action": {
  "action_str": "scroll(direction='down')",
  "action_description": "scroll on element with bid  in direction down",
  "action_output": {
    "thought": "",
    "action": {
      "delta_x": 0,
      "delta_y": 972
    },
    "action_name": "scroll"
  }
},
```