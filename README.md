mailtweets
============

A command line program to mail queried tweets

Information
-----------

This script queries tweets for given user(s), puts them in html format and send as mail to user. It was written with Python.

Requirements
------------

* Twitter developer account
* `pip install -r requirements.txt`

Usage
-----

* Get tweets of one user with default tweet count per user which is 10
    * `python mailtweets.py -u username`
* Get tweets of one user with given tweet count
    * `python mailtweets.py -u username -c number_of_tweets_per_user`
* Get tweets of users given in file with default tweet count
    * `python mailtweets.py -f filename`
* Get tweets of users given in file with given value
    * `python mailtweets.py -f filename -c number_of_tweets_per_user`
* Get tweets of users given in file by excluding specified usernames
    * `python mailtweets.py -f filename -e "username(s)_to_exclude_separated_by_spaces"`
* List top 10 trend topics for Turkey
    * `python mailtweets.py -tt`
