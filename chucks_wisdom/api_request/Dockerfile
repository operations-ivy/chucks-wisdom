FROM python:3.9

WORKDIR /usr/src/app

ADD api_request.py .

RUN pip3 install requests

CMD ["python", "./api_request.py"]
