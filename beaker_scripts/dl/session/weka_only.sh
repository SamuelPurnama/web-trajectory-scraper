# create a basic interactive session to inspect weka
beaker session create \
    --budget ai2/prior \
    --bare \
    --mount src=weka,ref=prior-default,dst=/root/weka/prior-default \
    --mount src=weka,ref=oe-training-default,dst=/root/weka/oe-training-default \
    --host-networking \
    --gpus 0
