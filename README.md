# any-json-to-metrics Prometheus exporter
This simple exporter parses any (I hope) JSON endpoints.

## Usage
All options should be set in 'exporter.json' file. There are only few options:
| Option | Type | Comment |
| ------ | ---- | ------- |
| bind_address | string | Interface address (default: "0.0.0.0") |
| port | int | TCP port (default: "9900") |
| prefix | string | (optional, default: "anyjson_") You can specify a prefix for all exporter's metrics (Prometheus "\_\_name\_\_") |
| data_types_in_name | bool | (optional, default: false) If "true" you will get types of elements in "\_\_name\_\_" | 
| endpoints | list of strings | Set all your endpoints |
| healthy_regex | list of strings | (optional) By default if the value of some JSON element is string, its metrics value will be 0. You can set regex to check these strings and value will set to 1 if string matches at least one regex. Compare anyjson_f and anyjson_f_state in the 1st example below. | 

Then just run it:
```
python exporter.py
```
or use Docker:
```
docker build -t any-json-to-metrics .
docker run -d -p 9900:9900 -v /path/to/exporter.json:/app/exporter.json any-json-to-metrics
```

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
