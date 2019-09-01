# -*- coding: iso-8859-1 -*-

import tweepy, sys
import xml.dom.minidom, xml.sax.saxutils
import simplejson as json
import logging
import splunk.entity as entity
import time
import os
import md5
import datetime

import httplib
from socket import timeout

SCHEME = """<scheme>
    <title>Twitter</title>
    <description>Continuously index all tweets that match a custom search query.</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>simple</streaming_mode>
    <endpoint>
        <args>
            <arg name="name">
                <title>Name</title>
                <description>Unique identifier for this Modular Input instance.</description>
            </arg>
            <arg name="API_KEY">
                <title>API_KEY</title>
                <description>Twitter API_KEY. See docs for details.</description>
            </arg>
            <arg name="API_SECRET">
                <title>API_SECRET</title>
                <description>Twitter API_SECRET. See docs for details.</description>
            </arg>
            <arg name="query">
                <title>Search query</title>
                <description>All tweets that match this query will be indexed. Supports AND/OR operators. See docs for details.</description>
            </arg>
        </args>
    </endpoint>
</scheme>
"""
# TODO add language param
# <arg name="lang">
#    <title>Language</title>
#    <description>Restricts tweets to the given language (ISO 639-1 code). Wildcard: *</description>
# </arg>

def do_scheme():
    print SCHEME

def validate_arguments(): 
    # TODO
    pass

def validate_conf(config, name): 
    # TODO
    pass

def get_encoded_file_path(config, query):
    # encode the query (simply to make the file name recognizable)
    name = ""
    for i in range(len(query)):
        if query[i].isalnum():
            name += query[i]
        else:
            name += "_"

    # MD5 the query
    m = md5.new()
    m.update(query)
    name += "_" + m.hexdigest()

    return os.path.join(config["checkpoint_dir"], name)

def save_checkpoint(config, query, tid):
    chk_file = get_encoded_file_path(config, query)
    logging.info("Checkpointing query=%s file=%s tid=%s", query, chk_file, tid)
    with open(chk_file, 'w+') as f:
        f.write(str(tid))
    f.close()

def read_checkpoint(config, query):
    chk_file = get_encoded_file_path(config, query)
    logging.info("Reading checkpoint for query=%s file=%s", query, chk_file)
    if (os.path.exists(chk_file)):
        with open(chk_file, 'r') as f:
            tid = int(f.read())
        f.close()
    else:
        tid = 0
    return tid

# Routine to get the values of an input
def get_config():

    # TODO implement logging

    config = {}

    try:
        # read everything from stdin
        config_str = sys.stdin.read()

        # parse the config XML
        doc = xml.dom.minidom.parseString(config_str)
        root = doc.documentElement
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data
                            #logging.debug("XML: '%s' -> '%s'" % (param_name, data))

        checkpnt_node = root.getElementsByTagName("checkpoint_dir")[0]
        if checkpnt_node and checkpnt_node.firstChild and \
           checkpnt_node.firstChild.nodeType == checkpnt_node.firstChild.TEXT_NODE:
            config["checkpoint_dir"] = checkpnt_node.firstChild.data

        if not config:
            raise Exception, "Invalid configuration received from Splunk."

        # just some validation: make sure these keys are present (required)
        validate_conf(config, "query")
        validate_conf(config, "API_KEY")
        validate_conf(config, "API_SECRET")
        validate_conf(config, "checkpoint_dir")

    except Exception, e:
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return config

# Routine to index data
def run_script(file_path): 

    config = get_config()
    
    auth = tweepy.AppAuthHandler(config["API_KEY"], config["API_SECRET"])
    api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)

    if (not api):
        # TODO implement logging
        print("Can't Authenticate")
        sys.exit(-1)

    query = config["query"]
    since_id = read_checkpoint(config, query)
    tweets_per_query = 100  # this is the max the API permits
    
    # TODO read language from config and insert into request query below
    lang = False

    max_id = -1
    tweet_count = 0
    new_since_id = False

    while tweet_count < 1000000:
        try:
            if max_id <= 0:
                new_tweets = api.search(
                    q=query,
                    count=tweets_per_query, 
                    since_id=since_id, 
                    tweet_mode='extended',
                    include_entities='false'
                    )
            else:
                new_tweets = api.search(
                    q=query,
                    count=tweets_per_query, 
                    max_id=str(max_id - 1), 
                    since_id=since_id, 
                    tweet_mode='extended',
                    include_entities='false'
                    )

            if not new_tweets:
                break            

            for tweet in new_tweets:

                data = {}
                data['_time'] = tweet.created_at.strftime("%Y-%m-%dT%H:%M:%S+00:00")
                data['full_text'] = tweet.full_text
                data['id'] = tweet.id
                data['in_reply_to_screen_name'] = tweet.in_reply_to_screen_name
                data['in_reply_to_status_id'] = tweet.in_reply_to_status_id
                data['in_reply_to_user_id'] = tweet.in_reply_to_user_id
                data['is_quote_status'] = tweet.is_quote_status
                data['lang'] = tweet.lang
                data['client'] = tweet.source

                if (tweet.place):
                    place = {}
                    if (tweet.place.name):
                        place['name'] = tweet.place.name
                    if (tweet.place.full_name):
                        place['full_name'] = tweet.place.full_name
                    if (tweet.place.country):
                        place['country'] = tweet.place.country
                    if (tweet.place.country_code):
                        place['country_code'] = tweet.place.country_code
                    if (tweet.place.place_type):
                        place['place_type'] = tweet.place.place_type
                    data['place'] = place

                if (tweet.coordinates):
                    data['coordinates'] = tweet.coordinates

                user = {}
                user['name'] = tweet.user.name
                user['screen_name'] = tweet.user.screen_name
                user['id'] = tweet.user.id
                user['verified'] = tweet.user.verified
                user['followers_count'] = tweet.user.followers_count
                user['friends_count'] = tweet.user.friends_count
                user['statuses_count'] = tweet.user.statuses_count
                user['listed_count'] = tweet.user.listed_count
                user['favourites_count'] = tweet.user.favourites_count
                user['created_at'] = tweet.user.created_at.strftime("%Y-%m-%dT%H:%M:%S+00:00")
                user['location'] = tweet.user.location
                user['lang'] = tweet.user.lang
                user['geo_enabled'] = tweet.user.geo_enabled
                user['profile_image_url'] = tweet.user.profile_image_url
                user['url'] = tweet.user.url

                data['user'] = user
                
                print(json.dumps(data, sort_keys=True))

            tweet_count += len(new_tweets)
            max_id = new_tweets[-1].id
            if not new_since_id:
                new_since_id = new_tweets[0].id

        except tweepy.TweepError as e:
            print("some error : " + str(e))
            break
    
    if new_since_id:
        save_checkpoint(config, query, new_since_id)


# Script must implement these args: scheme, validate-arguments
if __name__ == '__main__':
    script_dirpath = os.path.dirname(os.path.join(os.getcwd(), __file__))
    file_path = os.path.join(script_dirpath, "output.ojs")

    if len(sys.argv) > 1:
        if sys.argv[1] == "--scheme":
            do_scheme()
        elif sys.argv[1] == "--validate-arguments":
            validate_arguments()
        else:
            pass
    else:
        run_script(file_path)

    sys.exit(0)