import json
import os
import tempfile

import requests
from markdown_it import MarkdownIt
from markitdown import MarkItDown


def wikipedia_search(query: str, num_results: int = 10) -> dict:
    response = requests.get(
        "https://api.wikimedia.org/core/v1/wikipedia/en/search/page",
        params={"q": query, "limit": num_results},
        headers={
            "Authorization": os.getenv("WIKIPEDIA_ACCESS_TOKEN", None),
            "User-Agent": "web-wiki (tanmayg@allenai.org)",
        },
    )
    return dict(
        pages=response.json()["pages"] if response.status_code == 200 else [],
        response=response,
    )


def get_wiki_page_content(page: dict[str, str]) -> dict:
    response = requests.get(
        f"https://api.wikimedia.org/core/v1/wikipedia/en/page/{page['key']}/html",
        headers={
            "Authorization": os.getenv("WIKIPEDIA_ACCESS_TOKEN", None),
            "User-Agent": "web-wiki (tanmayg@allenai.org)",
        },
    )
    return dict(
        content=response.text if response.status_code == 200 else "",
        response=response,
    )


def convert_html_string_to_markdown(html_str) -> str:
    # Create a temporary file to save the HTML string
    with tempfile.NamedTemporaryFile(
        mode="w+", suffix=".html", delete=False
    ) as temp_html_file:
        # Write the HTML string to the temporary file
        temp_html_file.write(html_str)
        temp_html_file_path = temp_html_file.name

    md_str = ""
    try:
        md_str = MarkItDown().convert(temp_html_file_path).text_content
    finally:
        # Ensure the temporary file is deleted after conversion
        os.remove(temp_html_file_path)

    return md_str


def get_first_page_content(query: str) -> dict | None:
    pages = wikipedia_search(query, 1)["pages"]
    if len(pages) == 0:
        return None

    html_str = get_wiki_page_content(pages[0])["content"]
    if len(html_str) == 0:
        return None

    return dict(
        content=convert_html_string_to_markdown(html_str), page=pages[0]
    )


def extract_headings_from_markdown(md_str):
    # Initialize the Markdown parser
    md = MarkdownIt()
    tokens = md.parse(md_str)

    # Extract headings
    headings = []
    for token in tokens:
        if token.type == "heading_open":
            # The next token contains the heading content
            heading_level = int(token.tag[1])  # e.g., 'h1' -> 1
            heading_content = tokens[tokens.index(token) + 1].content
            headings.append(dict(level=heading_level, heading=heading_content))

    return headings


def extract_headings_and_content_from_markdown(markdown_text):
    # Initialize the Markdown parser
    md = MarkdownIt()
    tokens = md.parse(markdown_text)

    # Extract headings and their content
    sections = []
    current_section = None
    intro_content = ""  # To store content before the first heading

    for token in tokens:
        if token.type == "heading_open":
            # Save the current section if it exists
            if current_section:
                sections.append(current_section)

            # Start a new section
            heading_level = int(token.tag[1])  # e.g., 'h1' -> 1
            heading_content = tokens[tokens.index(token) + 1].content
            current_section = {
                "level": heading_level,
                "heading": heading_content,
                "content": "",
            }
        elif token.type == "paragraph_open":
            # Append paragraph content
            paragraph_content = tokens[tokens.index(token) + 1].content
            if current_section:
                current_section["content"] += paragraph_content + "\n"
            else:
                # If no heading yet, treat as intro content
                intro_content += paragraph_content + "\n"

    # Add the last section if it exists
    if current_section:
        sections.append(current_section)

    # Add intro content as a special section if it exists
    if intro_content.strip():
        sections.insert(
            0,
            {
                "level": 0,  # Level 0 to indicate it's not tied to a heading
                "heading": "",
                "content": intro_content.strip(),
            },
        )

    return sections


if __name__ == "__main__":
    res = get_first_page_content("joint")
    headings = extract_headings_from_markdown(res)
    sections = extract_headings_and_content_from_markdown(res)
    print(headings)

    import ipdb

    ipdb.set_trace()
