# script to create a beaker interactive session which mounts code from hostpath
# beaker image create used `bash scripts/create_image.sh`
# mount code directory and weka storage for storing results
# UV_PROJECT_ENVIRONMENT is the path where the virtual environment will be created when using `uv sync` or `uv run`
beaker session create \
    --budget ai2/prior \
    --bare \
    --image beaker://tanmayg/webolmo-synthetic-20250504190901 \
    --mount src=hostpath,ref=/data/tanmayg/Code/webolmo-synthetic,dst=/root/webolmo-synthetic \
    --mount src=weka,ref=oe-training-default,dst=/root/weka/oe-training-default \
    --secret-env OPENAI_API_KEY=TG_OPENAI_API_KEY \
    --secret-env BROWSERBASE_API_KEY=BROWSERBASE_API_KEY \
    --secret-env BROWSERBASE_PROJECT_ID=BROWSERBASE_PROJECT_ID \
    --host-networking
