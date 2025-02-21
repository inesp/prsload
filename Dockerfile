FROM python:3.13-slim

ENV HOST 0.0.0.0
ENV PORT 1234
ENV DEBUG true

COPY . /app
WORKDIR /app


RUN pip install -U setuptools pip
RUN pip install -r requirements.txt

EXPOSE 1234

CMD [ "flask", "run", "--host=0.0.0.0", "--port=1234"]
