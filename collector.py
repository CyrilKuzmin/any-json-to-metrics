import json
import requests
import time
import re

from prometheus_client import Metric

class JsonCollector(object):
    """
    JsonCollector как класс в целом необходим для работы с prometheus_client
    от которого не хочется отказываться. 

    Суть - получить json и сгенерировать на её основе метрики (Metric'и) в 
    формате OpenMetrics.

    Для начала работы инициализируем, передам config (dict) и endpoint (str)

    После запускаем collect()

    Основная логика в методе parse()

    """
    def __init__(self, config, endpoint):
        # по сути единственное обязательное поле
        self._endpoint = endpoint
        # все остальное
        self._healthy_regex = config.get("healthy_regex")
        self._prefix = config.get("prefix")
        self._show_type = config.get("data_types_in_name")

    def parse_base_turple(self, t: tuple, endpoint, label={}) -> dict:
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
        if isinstance(t[1], (int, float)):
            result["value"] = t[1]
        elif isinstance(t[1], bool):
            result["value"] = int(t[1])
        elif isinstance(t[1], str):
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

    def correct_metric_name(self, s: str) -> str:
        '''
        Все не буквы-цифры заменяем на "_", 
        после убираем эти подряд идущие символы 
        '''
        new = re.sub('[^a-zA-Z0-9]', '_', s)
        new = re.sub("_+", "_", new)
        return new

    def parse(self, t: tuple, metrics: list, endpoint, label={}) -> list:
        NoneType = type(None)
        if isinstance(t[1], (int, float, bool, str, NoneType)):
            mtr_d = {}
            if self._show_type:
                k = self.correct_metric_name(t[0]+'_value')
            else:
                k = self.correct_metric_name(t[0])
            v = t[1]
            mtr_d = self.parse_base_turple((k, v), endpoint, label=label)
            metric = Metric(mtr_d['name'], '', 'gauge')
            metric.add_sample(self._prefix + mtr_d['name'], value=mtr_d['value'], labels=mtr_d['labels'])
            metrics.append(metric)
        if isinstance(t[1], list):
            cnt = 0
            for i in t[1]:
                l = {"index": str(t[1].index(i))}
                name = f'{t[0]}_{cnt}'
                if self._show_type:
                    name += '_list'
                self.parse((name, i), metrics, endpoint, label=l)
                cnt += 1
        if isinstance(t[1], dict):
            for i in t[1].items():
                name = t[0]
                if self._show_type:
                    name += '_dict_'
                else:
                    name += '_'
                self.parse((name + i[0], i[1]), metrics, endpoint)

    def collect(self):
        # Получаем JSON
        data = {}
        metrics = []
        try:
            response = requests.get(self._endpoint)
            # По мимо метрик из json добавляем 2 дополнительные:
            # код ответа и успешность получения данных
            metric = Metric('response_code', '', 'gauge')
            metric.add_sample('response_code', value=response.status_code, labels={"url": self._endpoint})
            metrics.append(metric)
            metric = Metric('scrape_success', '', 'gauge')
            metric.add_sample('scrape_success', value=int(response.ok), labels={"url": self._endpoint})
            metrics.append(metric)
            data = response.json()
        except:
            metric = Metric('scrape_success', '', 'gauge')
            metric.add_sample('scrape_success', value=0, labels={"url": self._endpoint})
            metrics.append(metric)
        # тут может быть dict или list
        if type(data) == dict:
            for i in data.items():
                self.parse(i, metrics, self._endpoint)
        if type(data) == list:
            for elem in data:
                for i in elem.items():
                    self.parse(i, metrics, self._endpoint)
        # Генерируем
        for m in metrics:
            yield m
