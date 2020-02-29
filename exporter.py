from prometheus_client import start_http_server, Metric, REGISTRY
import json
import requests
import time
import re


class JsonCollector(object):
    def __init__(self, config):
        # по сути единственное обязательное поле
        self._endpoints = config["endpoints"]
        # все остальное
        self._healthy_regex = config.get("healthy_regex")
        self._prefix = config.get("prefix")
        self._show_type = config.get("data_types_in_name")

    def parseBaseTuple(self, t: tuple, endpoint, label={}) -> dict:
        '''
        Парсим "базовый" элемент типа ключ:значение,
        где ключ - str, значение - int,float,bool или str
        '''
        result = {
            "name": "",
            "value": 0,
            "labels": {"url": endpoint},
        }
        # имя метрики формируем как имена всех ключей до значения
        result["name"] += t[0]
        # само значение может быть 0, 1 или оно берется из json'ки, зависит от типа
        if type(t[1]) == (int or float):
            result["value"] = t[1]
        elif type(t[1]) == bool:
            result["value"] = int(t[1])
        elif type(t[1]) == str:
            result["labels"]["text"] = t[1]
            if self._healthy_regex:
                for r in self._healthy_regex:
                    if re.match(r, t[1]):
                        result["value"] = 1
        else:
            result["value"] = 0
        if label:
            result["labels"].update(label)
        return result

    def correctMetricName(self, s: str) -> str:
        return str(s).replace(' ', '_').replace('-','_')

    def parse(self, t: tuple, metrics: list, endpoint, label={}) -> list:
        NoneType = type(None)
        if type(t[1]) in (int, float, bool, str, NoneType):
            mtr_d = {}
            if self._show_type:
                k = self.correctMetricName(t[0]+'_value')
            else:
                k = self.correctMetricName(t[0])
            v = t[1]
            mtr_d = self.parseBaseTuple((k, v), endpoint, label=label)
            metric = Metric(mtr_d['name'], '', 'gauge')
            metric.add_sample(self._prefix + mtr_d['name'], value=mtr_d['value'], labels=mtr_d['labels'])
            metrics.append(metric)
        if type(t[1]) == list:
            for i in t[1]:
                l = {"index": str(t[1].index(i))}
                name = t[0]
                if self._show_type:
                    name += '_list'
                self.parse((name, i), metrics, endpoint, label=l)
        if type(t[1]) == dict:
            for i in t[1].items():
                name = t[0]
                if self._show_type:
                    name += '_dict_'
                else:
                    name += '_'
                self.parse((name + i[0], i[1]), metrics, endpoint)

    def collect(self):
        for endpoint in self._endpoints:
            # Получаем JSON
            data = {}
            metrics = []
            try:
                response = requests.get(endpoint)
                metric = Metric('responsecode', '', 'gauge')
                metric.add_sample(self._prefix + 'responsecode', value=response.status_code, labels={"url": endpoint})
                metrics.append(metric)
                metric = Metric('scrape_success', '', 'gauge')
                metric.add_sample(self._prefix + 'scrape_success', value=1, labels={"url": endpoint})
                metrics.append(metric)
                data = response.json()
            except:
                metric = Metric('scrape_success', '', 'gauge')
                metric.add_sample(self._prefix + 'scrape_success', value=0, labels={"url": endpoint})
                metrics.append(metric)
            # тут может быть dict или list
            if type(data) == dict:
                for i in data.items():
                    self.parse(i, metrics, endpoint)
            if type(data) == list:
                # Сделаю потом
                pass
            # Найти способ получше этих 2х строк...
            for m in metrics:
                yield m


if __name__ == '__main__':
    config = {}
    with open('exporter.json', 'r') as file:
        config = json.load(file)
    start_http_server(config["port"], addr=config["bind_address"])
    REGISTRY.register(JsonCollector(config))
    while True:
        time.sleep(1)
