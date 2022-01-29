from nltk import word_tokenize
from nltk.corpus import stopwords 
import re
from datetime import datetime

import pdb

TIMELIMIT = 120 #minutes

#Conversion to milliseconds
TIMELIMIT = TIMELIMIT * 60000 

def get_raw_comments(hot):
    #Return a list of lists representing the hot list
    #with each post being its own list of comments

    #List of lists containing lists with comment text
    hot_list = []
    index = 0
    for submission in hot:
        print('submission', submission, 'index:', index)
        if not submission.stickied:
            try:
                
                #print("Title: {}, ups: {}, downs: {}, ".format(submission.title,
                #                                               submission.ups,
                #                                               submission.downs))

                submission_comments = []
                submission.comments.replace_more(limit=0)
                for comment in submission.comments.list():
                    try:
                        now = datetime.utcnow().timestamp()
                        commentTime = comment.created_utc
                        
                        delta = now - commentTime
                        if delta <= TIMELIMIT: 
                            submission_comments.append(comment.body)
                        
                    except UnicodeEncodeError:
                        pass
                
                hot_list.append(submission_comments)
            except UnicodeEncodeError:
                pass
        index += 1
    print('submission comments parsed, returning...')
    return hot_list


def filter_comments(txt):
    """
    This function will preform basic filtering on a list
    of lists containing txt and return filtered txt.
    """
    #Remove stop words
    filt_comments = []
    for comment in txt:
        words = word_tokenize(comment)
        stop_words = set(stopwords.words("english"))
        
        #filter out stop words
        filt_words = [w for w in words if w not in stop_words]

        #Remove emojis
        no_emoji = " ".join(c for c in filt_words if c <= '\uFFFF')
        
        #Remove non alpha num
        S = re.sub(r'[^A-Za-z0-9 ]+', '', no_emoji)

        filt_comments.append(" ".join(S.split()))
    return filt_comments


def get_coin_price(public_key, secret_key, ticker, coin):
    coin = list(filter(lambda x: x['name'] == coin, ticker))[0]['priceUsd']
    return coin

    
    




