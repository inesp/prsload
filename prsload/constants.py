from datetime import datetime
from datetime import timedelta
from datetime import timezone

NUM_OF_DAYS = 40

BLOCKLISTED_REPOS = {
    "sleuth-io/sleuth-documentation-OLD",
    "sleuth-io/sleuth-pr",
    "sleuth-io/code-video-generator",
    "sleuth-io/netlify-plugin-sleuth",
    "sleuth-io/youtube-recorder",
    "sleuth-io/sleuth-export",
    "sleuth-io/test-repo",
    "sleuth-io/sleuth-deck",
    "sleuth-io/sleuth-sample-deploy",
    "sleuth-io/sleuth-marketing-site",
}
REVIEWERS_TO_IGNORE = {
    "IgorBogdanovskiSleuth",
    "daniel-dejuan-sleuth",
    "jjm",
    "kcb-sleuth",
    "adamchatko",
    "detkin",
    "cwgw",
    "zidarsk8",
}
PR_AUTHORS_TO_IGNORE = {
    "ptrikutam",
    "azamatsmith",
    "dependabot",
}

PRS_LIMIT = 100
PRS_FETCH_PAGES_LIMIT = 6

# TODO: Should we add this hike?? It messes with the numbers, but not in a predicable way..
NO_REVIEW_TIME_HIKE = timedelta(minutes=0)

VACATION = {
    "nejcambrozic": (datetime(2023, 5, 8, tzinfo=timezone.utc), datetime(2023, 5, 28, tzinfo=timezone.utc)),
    "mzgajner": (datetime(2023, 2, 13, tzinfo=timezone.utc), datetime(2023, 2, 18, tzinfo=timezone.utc)),
    "nhumrich": (datetime(2023, 4, 3, tzinfo=timezone.utc), datetime(2023, 4, 7, tzinfo=timezone.utc)),
    "davidpristovnik": (datetime(2023, 4, 24, tzinfo=timezone.utc), datetime(2023, 4, 26  , tzinfo=timezone.utc)),
}
