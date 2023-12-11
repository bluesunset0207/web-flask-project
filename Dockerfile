FROM python:3.12

COPY . /app

RUN pip3 install flask 

WORKDIR /app

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]