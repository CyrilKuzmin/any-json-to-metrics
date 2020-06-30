import json
import utils

from flask import Flask, request
from prometheus_client import Metric
from collector import JsonCollector

CONFIG = {}

app = Flask("any_json_to_metrics")

# Редиректим GET с корня на /metrics 
@app.route('/', methods=['GET'])
def redirect():
    return flask.redirect('/metrics')

# Prometheus-like обновление конфига. 
# Не прокатит для порта/интерфейса без рестарта
@app.route('/-/reload', methods=['POST'])
def reload():
    with open('exporter.json', 'r') as file:
        CONFIG = json.load(file)
    return "OK"

# Основная часть тут. Коллектим метрики, форматируем вывод.
# Форматирование взято из prometheus_client с выпиленной документацией 
# для метрик, ибо в нашем случае это 100% gauge и смысловой нагрузки нет
@app.route('/metrics', methods=['GET'])
def collect():
    output = []
    # JsonCollector (как того требует prometheus_client) имеет метод collect
    # который генерирует Metric'и. Эти метрики будут в формате OpenMetrics и их
    # надо преобразовать в формат прома, что и делается в блоке try
    # Потом эти метрики в виде готовых строк для прома идут в массив
    # output, что мы и возвращаем
    for metric in JsonCollector(CONFIG, request.args.get('target')).collect():
        try:
            mname = metric.name
            mtype = metric.type
            # Munging from OpenMetrics into Prometheus format.
            if mtype == 'counter':
                mname = mname + '_total'
            elif mtype == 'info':
                mname = mname + '_info'
                mtype = 'gauge'
            elif mtype == 'stateset':
                mtype = 'gauge'
            elif mtype == 'gaugehistogram':
                mtype = 'histogram'
            elif mtype == 'unknown':
                mtype = 'untyped'
            om_samples = {}
            for s in metric.samples:
                for suffix in ['_created', '_gsum', '_gcount']:
                    if s.name == metric.name + suffix:
                        # OpenMetrics specific sample, put in a gauge at the end.
                        om_samples.setdefault(suffix, []).append(utils.sample_line(s))
                        break
                else:
                    output.append(utils.sample_line(s))
        except Exception as exception:
            exception.args = (exception.args or ('',)) + (metric,)
            raise
        for suffix, lines in sorted(om_samples.items()):
            output.extend(lines)
    return ''.join(output).encode('utf-8')

if __name__ == '__main__':
    with open('exporter.json', 'r') as file:
        CONFIG = json.load(file)
    app.run(host=CONFIG["bind_address"], port=CONFIG["port"])