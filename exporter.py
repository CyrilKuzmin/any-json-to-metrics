import argparse
import json
import logging
import utils

from flask import Flask, request, redirect
from prometheus_client import Metric
from collector import JsonCollector

CONFIG = {}

app = Flask("any_json_to_metrics")

def init_logger():
    parser = argparse.ArgumentParser(description='any-json-to-metrics exporter')
    parser.add_argument("-log", "--log_level", help="set logger level (DEBUG, INFO, WARNING, ERROR). Default is INFO")
    args = parser.parse_args()
    if args.log_level is None:
        return
    # Валидируем введенный уровень
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        print('Invalid log level: %s' % args.log_level)
        exit(1)
    # Устанавливаем уровень
    logging.basicConfig(level=numeric_level)
    logw = logging.getLogger('werkzeug')
    logw.setLevel(numeric_level)

# Редиректим GET с корня на /metrics 
@app.route('/', methods=['GET'])
def redirect_to_metrics():
    return redirect('/metrics')

# Prometheus-like обновление конфига. 
# Не прокатит для порта/интерфейса без рестарта
@app.route('/-/reload', methods=['POST'])
def reload():
    with open('config.json', 'r') as file:
        CONFIG = json.load(file)
    return "OK"

# Основная часть тут. Коллектим метрики, форматируем вывод.
# Форматирование взято из prometheus_client с выпиленной документацией 
# для метрик, ибо в нашем случае это 100% gauge и смысловой нагрузки нет
@app.route('/metrics', methods=['GET'])
def collect():
    if not request.args.get('target'):
        return 'No target'
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
    init_logger()
    with open('config.json', 'r') as file:
        CONFIG = json.load(file)
    app.run(host=CONFIG["bind_address"], port=CONFIG["port"])
