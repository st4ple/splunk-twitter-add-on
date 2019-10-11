# :speech_balloon::electric_plug: Twitter Add-on for Splunk

> **WARNING**: This Splunk TA is still under construction. Future updates might break existing setups so proceed with care! 

## Installation
### Via GIT:
Clone this repository to $SPLUNK_HOME/etc/apps/ on an Indexer or Heavy Forwarder and restart Splunk.

````
$ git clone https://github.com/st4ple/splunk-twitter-add-on.git
$ splunk restart
````

#### Via Splunk UI:

Download the [ZIP directory of this repository](https://github.com/st4ple/splunk-twitter-add-on/archive/master.zip) and upload it to your Splunk instance via `Apps->Manage Apps->Install App from File`.


## Configuration 

Prerequisites: Consumer API key & secret for an App from the [Twitter Developer Portal](https://developer.twitter.com/en/apps).

#### Via Splunk UI:

Navigate to `Settings->Data inputs->Local Inputs->Twitter->New` and fill out the required parameters.

#### Via .conf files:

Add a stanza like this to an inputs.conf file (replace parts in <> brackets):

```YAML
[twitter://<unique stanza title>]
API_KEY = <twitter_api_key>
API_SECRET = <twitter_api_secret>
host = Twitter
index = <index>
interval = 300 
query = <your query or hashtag>
sourcetype = _json
```


## Example event:
```json
{
  "_time": "2019-10-09T18:00:01+00:00", 
  "client": "Sprinklr", 
  "full_text": "Python 3.7 is coming to Splunk. Download the Platform Upgrade Readiness app to help prepare for and manage this change.\nhttps://t.co/qSSeE8bxY4\n#Splunk", 
  "id": 1181992727409508352, 
  "in_reply_to_screen_name": null, 
  "in_reply_to_status_id": null, 
  "in_reply_to_user_id": null, 
  "is_quote_status": false, 
  "lang": "en", 
  "user": {
    "created_at": "2010-03-08T20:09:54+00:00", 
    "favourites_count": 266, 
    "followers_count": 6140, 
    "friends_count": 41, 
    "geo_enabled": true, 
    "id": 121214676, 
    "lang": null, 
    "listed_count": 136, 
    "location": "San Francisco, CA", 
    "name": "Splunk Answers", 
    "profile_image_url": "http://pbs.twimg.com/profile_images/1174294501633871872/AAK0906G_normal.jpg", 
    "screen_name": "splunkanswers", 
    "statuses_count": 82508, 
    "url": "http://t.co/eHyF0iwWdR", 
    "verified": false
  }
}
```
