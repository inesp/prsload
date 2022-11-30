from flask import Flask
import redis

app = Flask(__name__)
cache = redis.Redis(host="redis", port=6379)


@app.route("/")
def index():
    return "Congratulations, it's a web app!"
