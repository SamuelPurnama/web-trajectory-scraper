# create a basic interactive session to inspect weka
beaker session create \
    --budget ai2/prior \
    --bare \
    --mount src=weka,ref=oe-training-default,dst=/root/weka/oe-training-default \
    --secret-env OPENAI_API_KEY=PS_OPENAI_API_KEY \
    --secret-env BROWSERBASE_API_KEY=BROWSERBASE_API_KEY \
    --secret-env BROWSERBASE_PROJECT_ID=BROWSERBASE_PROJECT_ID \
    --host-networking \
    --gpus 0
