#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import smtplib
import getpass
import urllib3
from datetime import datetime, timedelta
from argparse import ArgumentParser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    import tweepy
except ImportError:
    print "tweepy module is required. Please run 'pip install -r requirements.txt'"
    sys.exit(1)

urllib3.disable_warnings()

access_token = os.environ['TWITTER_ACCESS_TOKEN']
access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']
consumer_key = os.environ['TWITTER_CONSUMER_KEY']
consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def get_last_n_tweets_of_user(username, number_of_tweets=10):
    """Return last n tweets of user as a dictionary. If latest tweet of user
    is older than a day, no tweet will be returned for this user.

    :type username: string
    :param username: username
    :type number_of_tweets: integer
    :param number_of_tweets: last n tweet requested (default = 10, max = 20)
    :rtype: dictionary
    :returns: last n tweets of given user
    """

    tweets = []
    user = api.get_user(username).name
    print "Getting tweets of %s" % user

    if number_of_tweets > 20:
        print "Max number of tweets allowed is 20"
        print "Getting last 20 tweets"
        number_of_tweets = 20

    user_tweets = api.user_timeline(username, count=number_of_tweets)

    last_tweet_time = user_tweets[0].created_at
    yesterday = datetime.now() - timedelta(hours=24)

    if last_tweet_time < yesterday:
        return {user: []}

    for tweet in user_tweets:
        if "https" in tweet.text:
            tweets.append(make_links_clickable(tweet))
        else:
            tweets.append(tweet.text)

    return {user: tweets}


def make_links_clickable(tweet):
    """Make links inside tweets clickable

    :type tweet: object
    :param tweet: a tweet of user
    :rtype: string
    :returns: modified tweet text that contains clickable links
    """

    # split tweet text
    tweet_splitted = tweet.text.split()

    # replace link text with clickable html link element
    for text_part in tweet_splitted:
        if text_part.startswith("https"):
            link_location = tweet_splitted.index(text_part)
            tweet_splitted[link_location] = "<a href='%s' style='color: #404040'>%s<a>" % (text_part, text_part)

    return ' '.join(tweet_splitted)


def get_all_tweets(filename, tweet_count=10, excluded_users=""):
    """Return all tweets belong to users in given file

    :type filename: string
    :param filename: name of file that contains usernames
    :type tweet_count: integer
    :param tweet_count: number of tweets requested per user (max=20)
    :type excluded_users: string
    :param excluded_users: list of users to exclude separated by spaces
    :rtype: dictionary
    :returns: a dictionary that contains username and list of tweets pairs
    """

    tweets = {}
    usernames = get_usernames_from_file(filename)

    if excluded_users:
        for username in excluded_users.split():
            if username in usernames:
                usernames.remove(username)

    for user in usernames:
        tweets.update(get_last_n_tweets_of_user(user, number_of_tweets=tweet_count))

    return tweets


def get_usernames_from_file(filename):
    """Get usernames from given file

    :type filename: string
    :param filename: name of file
    :rtype: list
    :returns: list of usernames(max = 10)
    """

    with open(filename) as users_file:
        usernames = users_file.read().splitlines()

    if not usernames:
        print "No username found in file! Exiting program..."
        sys.exit(1)

    if(len(usernames) > 10):
        print "Max username count supported is 10"
        print "Getting tweets of first 10 user"
        return usernames[:10]

    return usernames


def mail_tweets(tweets, mail_address):
    """Send tweets to given mail address

    :type tweets: string (html)
    :param tweets: tweets that constructed as html
    :type mail_address: string
    :param mail_address: mail address to send tweets
    """

    user_from = "<sender mail address>"
    pwd = getpass.getpass("Enter mail password: ")
    user_to = mail_address

    try:
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo()
        smtpserver.login(user_from, pwd)

    except smtplib.SMTPAuthenticationError:
        print "Password was incorrect! Please check it.\n"
        sys.exit(1)

    msg = MIMEMultipart("alternative")
    msg.set_charset("utf-8")
    msg["From"] = user_from
    msg["To"] = user_to
    msg["Subject"] = u'Recent Tweets'
    message_body = MIMEText(tweets, "html", "utf-8")
    msg.attach(message_body)

    smtpserver.sendmail(user_from, user_to, msg.as_string())
    smtpserver.close()

    print "Tweets were sent to given mail address"


def construct_html_message(tweets):
    """Return tweets formatted as html text

    :type tweets: dictionary
    :param tweets: a dictionary that contains username and list of tweets pairs
    :rtype: string
    :returns: tweets formatted as html
    """

    color_values = ["darkslategrey", "#FF3300", "#0000CC", "#009933", "#6600CC",
                    "#850C0C", "#3C3C0C", "#CC6600", "#666633", "#003300"]

    header_text = u"""<!DOCTYPE html>\n
    <html>
    <head>
        <meta content="text/html; charset=UTF-8" http-equiv="content-type">
        <title>Recent Tweets</title>
    </head>
    """

    body_text = "<body style='background-color: #E6E6E6;'>"

    index = 0
    for user_tweet in sorted(tweets.items()):

        body_text += u"<h2 style='color: %s; font-weight: normal; \
                        font-size: 2.2em;'>Tweets from %s</h2>" %(color_values[index], user_tweet[0])

        if not len(user_tweet[1]):
            body_text += u"\n<p style='color: #303030; font-size: 1.2em;'>No tweets for this user in last day.</p>"
            index += 1
            continue

        for tweet in user_tweet[1]:
            body_text += u"\n<p style='color: #303030; font-size: 1.2em;'>%s</p>" % tweet
            body_text += "<hr>"

        index += 1

    body_text += "\n</body>\n</html>"

    return header_text + body_text


if __name__ == '__main__':

    arg_parser = ArgumentParser()
    arg_parser.add_argument("-u", "--username", help="Twitter username of a user")
    arg_parser.add_argument("-c", "--count", default=10, type=int,
                            help="Number of tweets to query")
    arg_parser.add_argument("-f", "--filename", default="usernames.txt",
                            help="Name of file that contains usernames")
    arg_parser.add_argument("-e", "--exclude", help="User(s) to exclude")
    arg_parser.add_argument("-tt", "--trendtopics", action='store_true', help="List trend topics for Turkey")

    args = arg_parser.parse_args()

    if args.trendtopics:

        id_for_TR = 23424969
        trend_topics = api.trends_place(id_for_TR)

        print '{:40s} {}{:40s} {}'.format("Trend Topics", "Tweet Count\n", "------------", "-----------\n")

        for trend_topic in sorted(trend_topics[0]["trends"], key=lambda topic: topic["tweet_volume"], reverse=True)[:10]:
            try:
                tweet_count = int(trend_topic["tweet_volume"])
            except TypeError:
                tweet_count = 0

            tt_length = len(trend_topic["name"])
            tt_unicode_length = len(trend_topic["name"].encode("utf-8"))

            width = 40
            if tt_length != tt_unicode_length:
                width += tt_unicode_length - tt_length

            print '{:{width}s} {:11d}'.format(trend_topic["name"].encode("utf-8"), tweet_count, width=width)

        print

    tweets = {}

    if args.username and not args.count:
        # get tweets of one user with default n value that is 10
        tweets.update(get_last_n_tweets_of_user(args.username))

    elif args.username and args.count:
        # get tweets of one user with given value
        tweets.update(get_last_n_tweets_of_user(args.username, args.count))

    elif args.filename and not args.count:
        # get tweets of users given in file with default max last tweet value
        if args.exclude:
            tweets.update(get_all_tweets(args.filename, args.exclude))
        else:
            tweets.update(get_all_tweets(args.filename))

    elif args.filename and args.count:
        # get tweets of users given in file with given value
        if args.exclude:
            tweets.update(get_all_tweets(args.filename, args.count, args.exclude))
        else:
            tweets.update(get_all_tweets(args.filename, args.count))

    message = construct_html_message(tweets)

    mail_tweets(message, "<receiver mail address>")


