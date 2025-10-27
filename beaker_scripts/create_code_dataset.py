import os
from datetime import datetime

from beaker import Beaker

beaker_client = Beaker.from_env(default_workspace="ai2/webolmo")

files_to_upload = []
for root, dirs, filenames in os.walk("./"):
    # Skip .venv and .git directories
    dirs[:] = [
        d
        for d in dirs
        if d not in [".venv", ".git", ".zed", "__pycache__", "scratch"]
    ]
    for filename in filenames:
        if filename == "uv.lock":
            continue
        files_to_upload.append(os.path.join(root, filename))


timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
beaker_client.dataset.create(
    f"code-webolmo-synthetic-{timestamp}",
    *files_to_upload,
)

print(f"code-webolmo-synthetic-{timestamp}")
