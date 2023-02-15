from datetime import timedelta

NUM_OF_DAYS = 31

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
}
REVIEWERS_TO_IGNORE = {
    "IgorBogdanovskiSleuth",
    "daniel-dejuan-sleuth",
    "jjm",
    "kcb-sleuth",
    "adamchatko",
    "detkin",
    "cwgw",
}
PR_AUTHORS_TO_IGNORE = {
    "ptrikutam",
    "azamatsmith",
    "dependabot",
}

PRS_LIMIT = 100

# TODO: Should we add this hike?? It messes with the numbers, but not in a predicable way..
NO_REVIEW_TIME_HIKE = timedelta(minutes=0)
