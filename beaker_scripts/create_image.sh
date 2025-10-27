docker build -t webolmo-synthetic .
timestamp=$(date +%Y%m%d%H%M%S)
beaker image create --name webolmo-synthetic-$timestamp webolmo-synthetic --workspace ai2/webolmo
echo "Beaker image: webolmo-synthetic-$timestamp"
