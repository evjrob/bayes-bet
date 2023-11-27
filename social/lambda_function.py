from datetime import date
import os
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from tempfile import mkdtemp
import tweepy


def lambda_handler(event, context):
    # Check if the predictions have been updated before prodeeding
    url = event['url']
    response = requests.get(f"{url}/ready").json()
    if not response["ready_to_post"]:
        print("No current predictions to post. Exiting.")
        return

    # Set up Selenium with the Chromium driver
    options = webdriver.ChromeOptions()
    options.binary_location = '/opt/chrome/chrome'
    options.add_experimental_option("excludeSwitches", ['enable-automation'])
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--disable-client-side-phishing-detection')
    options.add_argument('--allow-running-insecure-content')
    options.add_argument('--disable-web-security')
    options.add_argument('--lang=en')
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")

    service = Service(executable_path='/opt/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(2000, 2000)

    # Navigate to the URL and screenshot the DOM element with id="screenshot"
    driver.get(url)
    element = driver.find_element(By.ID, "screenshot")
    element.screenshot("/tmp/screenshot.png")

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
    media_id = api.media_upload(filename="/tmp/screenshot.png").media_id_string

    # # Send the tweet with the media ID
    prediction_date = response["prediction_date"]
    pretty_date = date.fromisoformat(prediction_date).strftime("%B %d, %Y")
    tweet_message = f"BayesBet NHL game predictions for {pretty_date}: https://bayesbet.io/{prediction_date}/"
    client.create_tweet(text=tweet_message, media_ids=[media_id])
