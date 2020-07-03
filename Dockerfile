FROM python:alpine3.7

COPY exporter.py collector.py utils.py exporter.json requirements.txt /app/
RUN pip3 install -r /app/requirements.txt
EXPOSE 9900
WORKDIR /app

ENTRYPOINT [ "python", "exporter.py" ]