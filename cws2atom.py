# -*- coding: utf-8 -*-

# A script to retrieve Chrome Webstore reviews and support feedback and output them as an Atom feed to standard output

import sys
import datetime
import time
import random
import urllib.parse
import urllib.request
import json
import re

import pyatom

def get_comments(extension_id, group):
    request_url = "https://chrome.google.com/reviews/components"
    request_values = {
        "appId": 94,
        "version": "150922",
        "reqId": str(round(time.time()*1000)) + "-" + str(random.random()),
        "hl": "en",
        "specs": [  
            {  
                "type": "CommentThread",
                "url": urllib.parse.quote_plus("http://chrome.google.com/extensions/permalink?id=" + extension_id),
                "groups": group,
                "sortby": "date",
                "startindex": "0",
                "numresults": "100",
                "id": "1"
            }
        ],
        "internedKeys":[],
        "internedValues":[]
    }

    request_data = "req=" + json.dumps(request_values)
    request_data = request_data.encode("UTF-8")
    request = urllib.request.Request(request_url, request_data, headers={ "Content-Type": "text/plain;charset=UTF-8" })
    with urllib.request.urlopen(request) as response:
        response_encoding = response.headers["Content-Type"].split("charset=")[1]
        response_data = response.read().decode(response_encoding)
        matches = re.match(r"window\.google\.annotations2\.component\.load\(\{'1':\{'results':\{\"annotations\":\[(?P<reviews>.+)\]\,\"numAnnotations\":[0-9]+\,\"numAnnotationsAccuracy\":[0-9]+\,", response_data)
        return json.loads("[" + matches.group("reviews") + "]")

def process_reviews(extension_id, feed):
    for review in get_comments(extension_id, "chrome_webstore"):
        if "displayName" in review["entity"]:
            reviewer_name = review["entity"]["displayName"]
        else:
            reviewer_name = "(Anonymous)"
        feed.add(title="Review from " + reviewer_name + " - " + str(review["starRating"]) + "/5 stars",
                content="<p>Comment: " + review["comment"] + "</p>",
                content_type="html",
                updated=datetime.datetime.utcfromtimestamp(review["timestamp"]),
                url="https://chrome.google.com/webstore/detail/" + extension_id,
                id="review" + str(review["timestamp"]) + review["entity"]["shortAuthor"] + review["comment"]
        )

def process_support_feedback(extension_id, feed):
    for feedback in get_comments(extension_id, "chrome_webstore_support"):
        if "displayName" in feedback["entity"]:
            reporter_name = feedback["entity"]["displayName"]
        else:
            reporter_name = "(Anonymous)"
        feed.add(title="Feedback from " + reporter_name + ": " + str(feedback["title"]),
                content="<p>Comment: " + feedback["comment"] + "</p>",
                content_type="html",
                updated=datetime.datetime.utcfromtimestamp(feedback["timestamp"]),
                url="https://chrome.google.com/webstore/detail/" + extension_id,
                id="support" + str(feedback["timestamp"]) + feedback["entity"]["shortAuthor"] + feedback["comment"]
        )

if __name__ == "__main__":
    extension_id = sys.argv[1]

    def init_feed():
        return pyatom.AtomFeed(title="CWS: " + extension_id,
                    subtitle="Feed for reviews and support issues",
                    url="https://chrome.google.com/webstore/detail/" + extension_id)

    def exception_hook(*args):
        feed = init_feed()
        time_of_exception = datetime.datetime.utcnow()
        import traceback
        feed.add(title="Exception has occured!",
                content="<p>" + "<br />".join(traceback.format_exception(*args)) + "</p>",
                content_type="html",
                updated=time_of_exception,
                id=str(time_of_exception))
        print(feed.to_string())
        sys.exit()

    sys.excepthook = exception_hook

    feed = init_feed()

    process_reviews(extension_id, feed)
    process_support_feedback(extension_id, feed)

    print(feed.to_string())
