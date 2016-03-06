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
import copy

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

def get_comment_replies(extension_id, comment_list):
    request_url = "https://chrome.google.com/reviews/json/search"
    search_query_template =             {
        "requireComment": True,
        "entities": [
            {
                "annotation": {
                    "groups": None,
                    "author": None,
                    "url": "http://chrome.google.com/extensions/permalink?id=" + extension_id
                }
            }
        ],
        "matchExtraGroups": True,
        "startIndex": 0,
        "numResults": 100,
        "includeNicknames": True
    }
    request_values = {
        "applicationId": 94,
        "searchSpecs": []
    }

    id_to_index = dict()
    
    for comment in comment_list:
        if "replyExists" in comment["attributes"] and comment["attributes"]["replyExists"] is True:
            search_query = copy.deepcopy(search_query_template)
            search_query["entities"][0]["annotation"]["author"] = comment["entity"]["author"]
            search_query["entities"][0]["annotation"]["groups"] = comment["entity"]["groups"]
            request_values["searchSpecs"].append(search_query)

    request_data = "req=" + json.dumps(request_values)
    request_data = request_data.encode("UTF-8")
    request = urllib.request.Request(request_url, request_data, headers={ "Content-Type": "text/plain;charset=UTF-8" })
    with urllib.request.urlopen(request) as response:
        response_encoding = response.headers["Content-Type"].split("charset=")[1]
        response_data = response.read().decode(response_encoding)
        return json.loads(response_data)

def get_all_webstore_data(extension_id):
    comment_list = get_comments(extension_id, "chrome_webstore") + get_comments(extension_id, "chrome_webstore_support")
    comment_replies = get_comment_replies(extension_id, comment_list)
    comments_with_replies_count = 0
    for comment in comment_list:
        if "replyExists" in comment["attributes"] and comment["attributes"]["replyExists"] is True:
            comment["cws2atom_replies"] = comment_replies["searchResults"][comments_with_replies_count]["annotations"]
            comments_with_replies_count += 1
    return comment_list

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

    comments_with_replies_list = get_all_webstore_data(extension_id)

    for comment in comments_with_replies_list:
        if "displayName" in comment["entity"]:
            commenter_name = comment["entity"]["displayName"]
        else:
            commenter_name = "(Anonymous)"
        if "chrome_webstore" in comment["entity"]["groups"]:
            title = "Review - " + commenter_name + " - " + str(comment["starRating"]) + "/5 stars"
            feed.add(title=title,
                    content="<p>Comment: " + comment["comment"] + "</p>",
                    content_type="html",
                    updated=datetime.datetime.utcfromtimestamp(comment["timestamp"]),
                    url="https://chrome.google.com/webstore/detail/" + extension_id,
                    id="review" + str(comment["timestamp"]) + comment["entity"]["shortAuthor"] + comment["comment"]
            )
            if "cws2atom_replies" in comment:
                for comment_reply in comment["cws2atom_replies"]:
                    if "displayName" in comment_reply["entity"]:
                        replier_name = comment_reply["entity"]["displayName"]
                    else:
                        replier_name = "(Anonymous)"
                    feed.add(title="RE - " + replier_name + ": " + title,
                            content="<p>Comment reply: " + comment_reply["comment"] + "</p>",
                            content_type="html",
                            updated=datetime.datetime.utcfromtimestamp(comment_reply["timestamp"]),
                            url="https://chrome.google.com/webstore/detail/" + extension_id,
                            id="review_reply" + str(comment_reply["timestamp"]) + comment_reply["entity"]["shortAuthor"] + comment_reply["comment"]
                    )
        elif "chrome_webstore_support" in comment["entity"]["groups"]:
            title=comment["attributes"]["sfrAttributes"]["issueType"] + " - " + commenter_name + " - " + str(comment["title"])
            feed.add(title=title,
                    content="<p>App Version: " + comment["attributes"]["sfrAttributes"]["appVersion"] + "</p>" \
                        + "<p>Client Version: " + comment["attributes"]["sfrAttributes"]["clientVersion"] + "</p>" \
                        + "<p>Comment: " + comment["comment"] + "</p>",
                    content_type="html",
                    updated=datetime.datetime.utcfromtimestamp(comment["timestamp"]),
                    url="https://chrome.google.com/webstore/detail/" + extension_id,
                    id="support" + str(comment["timestamp"]) + comment["entity"]["shortAuthor"] + comment["comment"]
            )
            if "cws2atom_replies" in comment:
                for comment_reply in comment["cws2atom_replies"]:
                    if "displayName" in comment_reply["entity"]:
                        replier_name = comment_reply["entity"]["displayName"]
                    else:
                        replier_name = "(Anonymous)"
                    feed.add(title="RE - " + replier_name + ": " + title,
                            content="<p>Comment reply: " + comment_reply["comment"] + "</p>",
                            content_type="html",
                            updated=datetime.datetime.utcfromtimestamp(comment_reply["timestamp"]),
                            url="https://chrome.google.com/webstore/detail/" + extension_id,
                            id="support_reply" + str(comment_reply["timestamp"]) + comment_reply["entity"]["shortAuthor"] + comment_reply["comment"]
                    )

    print(feed.to_string())
