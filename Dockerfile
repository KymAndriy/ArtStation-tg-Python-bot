FROM ubuntu:20.04

WORKDIR ~

COPY requirements.txt bot_configs.json bot.py ./

RUN cat requirements.txt

RUN apt-get update 
RUN apt-get install -y python3 python3-pip
RUN pip install -r requirements.txt

CMD python3 bot.py
