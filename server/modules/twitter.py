import tweepy
from tweepy import TweepError
import pandas as pd
import time
import os
import requests
import csv
import io
from .moduleimpl import ModuleImpl
from server.models import ChangeDataVersionCommand
from .utils import *

# ---- Twitter ----

class Twitter(ModuleImpl):

    # Must match order of items in twitter.json module def
    QUERY_TYPE_USER = 0
    QUERY_TYPE_SEARCH = 1

    # Get dataframe of last tweets fron our storage,
    @staticmethod
    def get_stored_tweets(wf_module):
        tablestr = wf_module.retrieve_data()
        if (tablestr != None) and (len(tablestr) > 0):
            return pd.read_csv(io.StringIO(tablestr))
        else:
            return None

    # Get from Twitter, return as dataframe
    @staticmethod
    def get_new_tweets(wfm, querytype, query, old_tweets):

        # Authenticate with "app authentication" mode (high rate limit, read only)
        consumer_key = os.environ['CJW_TWITTER_CONSUMER_KEY']
        consumer_secret = os.environ['CJW_TWITTER_CONSUMER_SECRET']
        auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
        api = tweepy.API(auth)

        # Only get last 100 tweets, because that is twitter API max for single call
        if querytype == Twitter.QUERY_TYPE_USER:
            tweetsgen = api.user_timeline(query, count=200)
        else:
            tweetsgen = api.search(q=query, count=100)

        # Columns to retrieve and store from Twitter
        # Also, we use this to figure ou the index the id field when merging old and new tweets
        cols = ['id', 'created_at', 'text', 'in_reply_to_screen_name', 'in_reply_to_status_id', 'retweeted',
                'retweet_count', 'favorited', 'favorite_count', 'source']

        tweets = [[getattr(t, x) for x in cols] for t in tweetsgen]
        table = pd.DataFrame(tweets, columns=cols)
        return table


    # Combine this set of tweets with previous set of tweets
    def merge_tweets(wf_module, new_table):
        old_table = Twitter.get_stored_tweets(wf_module)
        if old_table is not None:
            new_table = pd.concat([new_table,old_table]).drop_duplicates(['id']).sort_values('id',ascending=False).reset_index(drop=True)
        return new_table

    # Render just returns previously retrieved tweets
    @staticmethod
    def render(wf_module, table):
        return Twitter.get_stored_tweets(wf_module)


    # Load specified user's timeline
    @staticmethod
    def event(wfm, parameter, e):
        table = None

        # fetching could take a while so notify clients/users that we're working on it
        wfm.set_busy(notify=True)

        try:
            querytype = wfm.get_param_menu_idx("querytype")
            query = wfm.get_param_string('query')

            if wfm.get_param_checkbox('accumulate'):
                old_tweets = Twitter.get_stored_tweets(wfm)
                tweets = Twitter.get_new_tweets(wfm, querytype, query, old_tweets)
                tweets = Twitter.merge_tweets(wfm, tweets)
            else:
                tweets = Twitter.get_new_tweets(wfm, querytype, query, None)

        except TweepError as e:
            if querytype==Twitter.QUERY_TYPE_USER and e.response.status_code==401:
                wfm.set_error('User %s\'s tweets are protected' % query)
                return
            elif querytype==Twitter.QUERY_TYPE_USER and e.response.status_code==404:
                wfm.set_error('User %s does not exist' % query)
                return
            else:
                wfm.set_error('HTTP error %s fetching tweets' % str(e.response.status_code))
                return

        except Exception as e:
            wfm.set_error('Error fetching tweets: ' + str(e))
            return


        if wfm.status != wfm.ERROR:

            wfm.set_ready(notify=False)
            new_csv = tweets.to_csv(index=False)  # index=False to prevent pandas from adding an index col

            # Change the data version (when new data found) only if this module set to auto update, or user triggered
            auto = wfm.auto_update_data or (e is not None and e.get('type') == "click")

            # Also notifies client
            save_data_if_changed(wfm, new_csv, auto_change_version=auto)



