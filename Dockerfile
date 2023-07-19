FROM python:3.11

WORKDIR /code

COPY ./ /code/

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./src /code/src
 
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
