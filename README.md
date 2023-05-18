# See stats about PR reviews

Get an [API access token from GitHub](https://github.com/settings/tokens) and put it into your `.env` file (on root):
```
GITHUB_API_TOKEN=gho_8765...............
```

Start the code with 

```shell
make build up
```

Open the page [http://127.0.0.1:1234/top_reviewers](http://127.0.0.1:1234/top_reviewers).

## Details:

We fetch a LOT of data and it can take several minutes. For this reason, we cache GH data in redis for this
`prsload/redis_prs.py::CACHE_DURATION` long.

For this reason the first load might be very slow, but consecutive page refresh will be much faster. BUT! it also
won't show latest data, but cached data.

Look at `/prsload/constants.py` to modify constants like:
- vacation times
- users to ignore
- ...
