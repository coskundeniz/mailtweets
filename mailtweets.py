#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import tweepy
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


access_token = "<access_token>"
access_token_secret = "<access_token_secret>"
consumer_key = "<consumer_key>"
consumer_secret = "<consumer_secret>"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def get_last_n_tweets_of_user(username, number_of_tweets=10):
    """Return last n tweets of user as a dictionary

    :type username: string
    :param username: username
    :type number_of_tweets: integer
    :param number_of_tweets: last n tweet requested (default = 10, max = 20)
    :rtype: dictionary
    :returns: last n tweets of given user
    """

    user = api.get_user(username).name
    print "Getting tweets of %s" % user
 
    if number_of_tweets > 20:
        print "Max number of tweets allowed is 20"
        print "Getting last 20 tweets"
        number_of_tweets = 20 

    user_tweets = api.user_timeline(username, count=number_of_tweets)
    
    tweets = [tweet.text for tweet in user_tweets]

    return {user: tweets}


def get_all_tweets(filename, tweet_count=10):
    """Return all tweets belong to users in given file

    :type filename: string
    :param filename: name of file that contains usernames
    :type tweet_count: integer
    :param tweet_count: number of tweets requested per user (max=20)
    :rtype: dictionary
    :returns: a dictionary that contains username and list of tweets pairs
    """

    tweets = {}
    usernames = get_usernames_from_file(filename)

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
    pwd = "<password>"
    user_to = mail_address
    
    smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(user_from, pwd)

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

    header_text = u"""<!DOCTYPE html>\n
    <html>
    <head>
        <meta content="text/html; charset=UTF-8" http-equiv="content-type">
        <title>Recent Tweets</title>
    </head>
    """

    body_text = "<body style='background-color: #E6E6E6;'>"
    
    for user, user_tweets in tweets.iteritems():
        body_text += u"<h2 style='color: darkslategrey; font-weight: normal; \
                        font-size: 2.2em;'>Tweets from %s</h2>" % user

        for tweet in user_tweets:
            body_text += u"\n<p style='color: #303030; font-size: 1.2em;'>%s</p>" % tweet
            body_text += "<hr>"
        
    body_text += "\n</body>\n</html>"

    return header_text + body_text


def usage():
    return """Please give correct parameters  
    
    Possible usage scenarios
    ------------------------
    * python get_tweets.py <username> 
    * python get_tweets.py <username> <number of tweets> 
    * python get_tweets.py <-f> <filename>
    * python get_tweets.py <-f> <filename> <number of tweets>
    """


if __name__ == '__main__':

    tweets = {}

    if(len(sys.argv) == 2):
        # get tweets of one user with default n value that is 10
        tweets.update(get_last_n_tweets_of_user(sys.argv[1]))

    elif(len(sys.argv) == 3 and sys.argv[1] != "-f"):
        # get tweets of one user with given value 
        tweets.update(get_last_n_tweets_of_user(sys.argv[1], int(sys.argv[2])))

    elif(len(sys.argv) == 3 and sys.argv[1] == "-f"):
        # get tweets of users given in file with default max last tweet value
        tweets.update(get_all_tweets(sys.argv[2]))

    elif(len(sys.argv) == 4 and sys.argv[1] == "-f"):
        # get tweets of users given in file with given value
        tweets.update(get_all_tweets(sys.argv[2], int(sys.argv[3])))

    else:
        print usage()
    
    message = construct_html_message(tweets)

    mail_tweets(message, "<receiver mail address>")

