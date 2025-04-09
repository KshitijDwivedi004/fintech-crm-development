FROM python:3.10

EXPOSE 80

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install -r /code/requirements.txt

RUN apt-get -y clean

COPY ./api /code/api
COPY ./bot /code/bot

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]