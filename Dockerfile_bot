FROM python:3.12


COPY requirements.txt /botapp/
WORKDIR /botapp

RUN apt-get -y update && apt-get install -y --no-install-recommends ffmpeg

RUN pip install -r requirements.txt

ENV PYTHONPATH=/botapp

COPY . .
CMD ["python3", "bot/main.py"]