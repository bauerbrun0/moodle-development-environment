FROM python:3

WORKDIR /usr/src/app

RUN mkdir moodle_data
RUN apt-get update \
    && apt-get install -y wget \
    && apt-get install -y unzip


RUN wget https://github.com/elementx-ai/moodle-local-oauth/releases/download/v1.0.6/oauth-1.0.6.zip
RUN unzip oauth-1.0.6.zip
RUN rm oauth-1.0.6.zip


RUN pip install mysql-connector-python

COPY script.py .

CMD [ "python", "-u", "./script.py" ]