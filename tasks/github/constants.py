FIELD_TO_KEYWORDS = {
    "web_development": [
        "nextjs", "tailwindcss", "react hooks", "fullstack", "nodejs",
        "auth", "typescript", "express", "graphql", "web3"
    ],
    "ai_machine_learning": [
        "llm", "transformers", "diffusion models", "openai api", "langchain",
        "multi-modal models", "autogpt", "text generation", "agent", "prompt engineering",
        "post training", "reinforcement learning", "stable diffusion"
    ],
    "data_science": [
        "pandas projects", "data visualization", "notebooks", "EDA", "streamlit",
        "time series", "dashboards", "feature engineering", "data pipeline", "statistics"
    ],
    "mobile_app_development": [
        "flutter", "react native", "android jetpack", "ios swiftui", "firebase auth",
        "push notifications", "mobile ui kit", "camera app", "offline storage", "cross-platform"
    ],
    "game_development": [
        "unity3d", "godot engine", "unreal engine", "game physics", "2d platformer",
        "multiplayer game", "procedural generation", "game ai", "open world", "pixel art game"
    ],
    "bioinformatics": [
        "genomics", "sequencing", "proteomics", "metabolomics", "biostatistics", "bioinformatics tools",
        "genetic algorithms", "biological databases", "sequence alignment", "phylogenetics", "CRISPR"
    ]
}


FIELD_TO_KEYWORDS["awesome"] = [f"awesome {kw}" for kw in FIELD_TO_KEYWORDS["ai_machine_learning"]]

LANGUAGES = ["python", "javascript", "java", "c++",  "c#", "c", "go", "ruby", "html", "php", "matlab"]

REPO_SORT_CRITERIA = [
    "best match",
    "most stars",
    "fewest stars",
    "most forks",
    "fewest forks",
    "recently updated",
    "least recently updated",
]
