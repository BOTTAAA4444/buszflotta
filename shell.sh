curl -X PUT "localhost:9200/_index_template/bus_telemetry_template" -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["bus-telemetry-*"],
  "template": {
    "mappings": {
      "properties": {
        "location": { "type": "geo_point" },
        "@timestamp": { "type": "date" }
      }
    }
  }
}'
