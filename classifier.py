import os
import praw
import json
from datetime import datetime as DT
import nltk
from nltk import word_tokenize
from comment_util import get_raw_comments, filter_comments, get_coin_price
import json
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from decouple import config
from pymongo import MongoClient
import boto3
import pdb
import uuid
import shrimpy

# defining all the coins we lookup, here
COINS = [
    { "name": 'bitcoin', "ticker": 'btc' },
    { "name": 'ethereum', "ticker": 'eth' },
    { "name": 'dogecoin', "ticker": 'doge' },
    { "name": 'chainlink', "ticker": 'link' },
    { "name": 'polkadot', "ticker": 'dot' },
]

class DBConnectionError(Exception):
    """Raised when something goes wrong with DynamoDB connection handling"""
    pass

def classifier(client_id, client_secret, password, user_agent, username, num_posts, shrimpy_pub_key, shrimpy_priv_key):
    nltk.download('punkt')
    nltk.download('stopwords')
    start = DT.now()    
    print('start: ', start)
    # can't have a count less than one, so initializing to a non value
    tally = {
        "bitcoin": -1,
        "ethereum": -1,
        "dogecoin": -1,
        "chainlink": -1,
        "polkadot": -1,
    }
    scoreKeeper = {}

    # TODO: this should be an environment setting...
    print('requesting reddit API...')
    # TODO: these NEED to be set from environment!

    reddit = praw.Reddit(client_id=client_id,
                        client_secret=client_secret,
                        password=password,
                        user_agent=user_agent,
                        username=username)
    """
    ________________________________Getting Coin Prices_____________________________________________
    """
    ticker = ''
    client = shrimpy.ShrimpyApiClient(shrimpy_pub_key, shrimpy_priv_key)

    try:
        ticker = client.get_ticker('kucoin')
    except:
        try:
            ticker = client.get_ticker('binance')
        except:
            try:
                ticker = client.get_ticker('kraken')
            except:
                print("FAILED TO GET COIN PRICE!")
                return None 
    
    #Get BitCoin Price
    bitcoin_price = get_coin_price(shrimpy_pub_key, shrimpy_priv_key, ticker, 'Bitcoin')
    ethereum_price = get_coin_price(shrimpy_pub_key, shrimpy_priv_key, ticker, 'Ethereum')
    dogecoin_price = get_coin_price(shrimpy_pub_key, shrimpy_priv_key, ticker, 'Dogecoin')
    chainlink_price = get_coin_price(shrimpy_pub_key, shrimpy_priv_key, ticker, 'Chainlink')
    polkadot_price = get_coin_price(shrimpy_pub_key, shrimpy_priv_key, ticker, 'Polkadot')

    prices = {"bitcoin": bitcoin_price,
              "ethereum": ethereum_price,
              "dogecoin": dogecoin_price,
              "chainlink": chainlink_price,
              "polkadot": polkadot_price
              }


    """
    _________________________________________________________________________________________________
    """

    # TODO: Consider how to implement multiple subreddit requests at the same time
    
    print('parsing reddit API response for /r/CryptoCurrency...')
    # This gets the hot recent posts for the following subreddits - and the currencies:
    # 1. r/CryptoCurrency - all crypto (seems to focus on BTC/ETH)
    # 2. r/ethereum - ethereum
    # 3. r/dogecoin - dogecoin
    # 4. r/Chainlink - chainlink
    # 5. r/dot - polkadot
    # 6. r/Bitcoin - bitcoin
    subreddit = reddit.subreddit('CryptoCurrency+ethereum+dogecoin+Chainlink+dot+Bitcoin')
    hot_wsb = subreddit.hot(limit=num_posts)
    raw_txt = get_raw_comments(hot_wsb)

    print('starting comments filter...')
    filter_comments_list = list(map(filter_comments, raw_txt))

    print('filter_comments_list generated')
    filtered_txt = filter_comments_list

    analyzer = SentimentIntensityAnalyzer()

    print('starting comment analyzer...')
    
    for idx, post in enumerate(filtered_txt):
        for comment in post:
            sentiment = analyzer.polarity_scores(comment)['compound']
            score = 0
            if sentiment < -0.05:
                score = -1
            elif -0.05 <= sentiment <= 0.05:
                score = 0
            else:
                score = 1
        
            txt = word_tokenize(comment)
            
            for coin in COINS:
                for word in txt:
                    if word.lower() == coin['name'] or word.lower() == coin['ticker']:
                        if tally[coin['name']] == -1:
                            tally[coin['name']] = 1
                            scoreKeeper[coin['name']] = score
                        else:
                            tally[coin['name']] += 1
                            scoreKeeper[coin['name']] += score
        print('post', idx, 'finished')


    # for now, collecting all mentioned stocks, but separating the 10 most positive and the most negative
    timestamp = DT.utcnow()
    result = { "raw": [], "topPositive": [], "topNegative": [], "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S%zZ") }
    for key in (tally.keys()):
        if tally[key] > 1:
            coinObj = {
                "name": key,
                "tally": tally[key],
                "score": scoreKeeper[key],
                "price": prices[key],
                "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S%zZ")
            }
           
            if coinObj["score"] != None and coinObj["tally"] != None:
                result["raw"].append(coinObj)

    # iterate over raw, now collect top 10 and bottom 10 according to sentiment scores
    result["raw"] = sorted(result["raw"], key=lambda coin: coin["score"], reverse=True)
    delta = DT.now() - start

    print("script took {}".format(delta))
    return result, timestamp

class DBConnectionError(Exception):
    """Raised when something goes wrong with DynamoDB connection handling"""
    pass

def write_to_db(output_data, timestamp):
    try:
        AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
        AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY')
        AWS_DEFAULT_REGION = config('AWS_DEFAULT_REGION')
        # manually setting the enviornment so less of the Dockerfile has to change
        # and ease of config for boto3 (AWS client for python)
        os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
        os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY
        os.environ['AWS_DEFAULT_REGION'] = AWS_DEFAULT_REGION
        # adding unique key to each document because dynamoDB doesn't
        print('attempting to connect to db...')
        output_data['dateMonth'] = timestamp.strftime("%Y-%m")
        output_data['timestamp'] = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('sentimentData')
        result = table.put_item(Item=output_data, ReturnValues='ALL_OLD')
        print(result)
        if result['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise DBConnectionError
    except Exception as err:
        print('ERR insert failed:', err)

if __name__ == '__main__':
    CLIENT_ID = config('CLIENT_ID')
    CLIENT_SECRET = config('CLIENT_SECRET')
    PASSWORD = config('PASSWORD')
    USER_AGENT = config('USER_AGENT')
    USERNAME = config('USERNAME')
    NUM_POSTS = config('NUM_POSTS', default=100, cast=int)

    # Shrimpy stuff
    
    SHRIMPY_PUB_KEY = config('PUBLIC_KEY')
    SHRIMPY_PRIV_KEY = config('PRIVATE_KEY')
    
    output_data, timestamp = classifier(CLIENT_ID, CLIENT_SECRET, PASSWORD, USER_AGENT, USERNAME, NUM_POSTS, SHRIMPY_PUB_KEY, SHRIMPY_PRIV_KEY)

    write_to_db(output_data, timestamp)
