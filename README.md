# any-json-to-metrics Prometheus exporter
This simple exporter parses any (I hope) JSON endpoints.

## Usage

### Configuration and running
All options should be set in 'config.json' file. There are only few options:
| Option | Type | Comment |
| ------ | ---- | ------- |
| bind_address | string | Interface address (default: "0.0.0.0") |
| port | int | TCP port (default: "9900") |
| prefix | string | (optional, default: "anyjson_") You can specify a prefix for all exporter's metrics (Prometheus "\_\_name\_\_") |
| data_types_in_name | bool | (optional, default: false) If "true" you will get types of elements in "\_\_name\_\_" | 
| healthy_regex | list of strings | (optional) By default if the value of some JSON element is string, its metrics value will be 0. You can set regex to check these strings and value will set to 1 if string matches at least one regex. Compare anyjson_f and anyjson_f_state in the 1st example below. | 

Then just run it:
```
python exporter.py
```
or use Docker:
```
docker build -t any-json-to-metrics .
docker run -d -p 9900:9900 -v /path/to/config.json:/app/config.json -name any-json-to-metrics any-json-to-metrics
```

### Prometheus config
The sample config:
```
global:
    scrape_interval: 15s
    scrape_timeout: 10s
    evaluation_interval: 15s
scrape_configs:
  - job_name: "any-json"
    metrics_path: /metrics
    static_configs:
      - targets:
          - http://localhost:5000/appmetrics_bad.json
          - http://localhost:5000/appmetrics_ok.json
          - http://localhost:5000/invalid_json.json
          - http://localhost:5000/list.json
          - http://localhost:5000/manystrings.json
          - http://localhost:5000/rfc.json
          - http://localhost:5000/sentry_bad.json
          - http://localhost:5000/sentry_ok.json
          - http://localhost:5000/simple.json
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9900
```
You must specify all endpoints as targets and apply relabel config.
IMHO it's the best way to maintain a relevant config and list of all endpoints.

Run prometheus for tests:
```
sudo docker run -d \
    -p 9090:9090 \
    --network="host" \
    -v /tmp/prometheus_sample.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus
```
### Grafana dashboard example
![Grafana dashboard example](/grafana70_example.png?raw=true "Grafana dashboard example")
### Test server
```
cd tests
python test_server.py
```
It just looks for json files in the directory and returns them.

## Examples
Input:
```
{
    "a": 1234, 
    "b": [4,8,15,16], 
    "d": false, 
    "f": "sometext", 
    "f_state": "Healthy text", 
    "g": 
    {
        "k": 
        {
            "k": 12
        }, 
            "id": "error"
    }
}
```
Output:
```
anyjson_responsecode{job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	200
anyjson_scrape_success{job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	1
anyjson_a{job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	1234
anyjson_d{job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	0
anyjson_f{job="any-json-to-metrics",text="sometext",url="http://localhost:5000/simple.json"}	0
anyjson_f_state{job="any-json-to-metrics",text="Healthy text",url="http://localhost:5000/simple.json"}	1
anyjson_g_k_k{job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	12
anyjson_g_id{job="any-json-to-metrics",text="error",url="http://localhost:5000/simple.json"}	0
anyjson_b{index="0",job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	4
anyjson_b{index="1",job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	8
anyjson_b{index="2",job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	15
anyjson_b{index="3",job="any-json-to-metrics",url="http://localhost:5000/simple.json"}	16
```

Input:
```
{
    "healthy": {
        "admin-api": "OK. 'http://admin-api/health' success. Total Time taken: 123ms. Attempts: 1.",
        "db_check": "Ok",
        "service-one": "OK. 'http://service-one/health' success. Total Time taken: 26ms. Attempts: 1.",
        "service-two": "OK. 'http://service-two/health' success. Total Time taken: 1ms. Attempts: 1.",
        "service-scheduler": "OK. 'http://scheduler/health' success. Total Time taken: 2ms. Attempts: 1."
    },
    "status": "Healthy"
}
```
Output:
```
anyjson_responsecode{job="any-json-to-metrics",url="http://localhost:5000/appmetrics_ok.json"}	200
anyjson_scrape_success{job="any-json-to-metrics",url="http://localhost:5000/appmetrics_ok.json"}	1
anyjson_healthy_admin_api{job="any-json-to-metrics",text="OK. 'http://admin-api/health' success. Total Time taken: 123ms. Attempts: 1.",url="http://localhost:5000/appmetrics_ok.json"}	1
anyjson_healthy_db_check{job="any-json-to-metrics",text="Ok",url="http://localhost:5000/appmetrics_ok.json"}	1
anyjson_healthy_service_one{job="any-json-to-metrics",text="OK. 'http://service-one/health' success. Total Time taken: 26ms. Attempts: 1.",url="http://localhost:5000/appmetrics_ok.json"}	1
anyjson_healthy_service_two{job="any-json-to-metrics",text="OK. 'http://service-two/health' success. Total Time taken: 1ms. Attempts: 1.",url="http://localhost:5000/appmetrics_ok.json"}	1
anyjson_healthy_service_scheduler{job="any-json-to-metrics",text="OK. 'http://scheduler/health' success. Total Time taken: 2ms. Attempts: 1.",url="http://localhost:5000/appmetrics_ok.json"}	1
anyjson_status{job="any-json-to-metrics",text="Healthy",url="http://localhost:5000/appmetrics_ok.json"}	1
```


