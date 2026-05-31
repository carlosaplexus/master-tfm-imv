#!/bin/sh
echo "▶ Ejecutando todos los scripts K6..."
for f in /scripts/*.js; do
  name=$(basename "$f" .js)
  echo "▶ Ejecutando $name"
  k6 run --tag script_name=$name --tag pipeline_id=$PIPELINE_ID "$f"
done
