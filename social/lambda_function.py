import os
import tweepy
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service


def lambda_handler(event, context):
    # Set up Selenium with the Chromium driver
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(2000, 2000)

    # Navigate to the URL and screenshot the DOM element with id="screenshot"
    url = event['url']
    driver.get(url)
    element = driver.find_element(By.ID, "screenshot")
    element.screenshot("screenshot.png")

    driver.quit()

    # Fetch the Twitter API keys and secrets from environment variables
    bearer_token = os.environ['TWITTER_BEARER_TOKEN']
    consumer_key = os.environ['TWITTER_CONSUMER_KEY']
    consumer_secret = os.environ['TWITTER_CONSUMER_SECRET']
    access_token = os.environ['TWITTER_ACCESS_TOKEN']
    access_token_secret = os.environ['TWITTER_ACCESS_TOKEN_SECRET']

    # Set up Tweepy with the Twitter API keys and secrets
    auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)
    
    client = tweepy.Client(
        bearer_token=bearer_token,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        access_token=access_token,
        access_token_secret=access_token_secret,
        wait_on_rate_limit=True,
    )

    # # Upload the screenshot to Twitter and get the media ID
    media_id = api.media_upload(filename="screenshot.png").media_id_string

    # # Send the tweet with the media ID
    tweet_message = event['tweet_message']
    client.create_tweet(text=tweet_message, media_ids=[media_id])
