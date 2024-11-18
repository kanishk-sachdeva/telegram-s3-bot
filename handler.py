import json
import os
import boto3
import requests
from botocore.exceptions import NoCredentialsError, ClientError
import asyncio
from pprint import pprint
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize S3 client
s3 = boto3.client('s3')

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_API")
bucket_name = os.getenv("BUCKET_NAME")
telegram_error_group = os.getenv("TELEGRAM_ERROR_GROUP")
telegram_channel_req = os.getenv("TELEGRAM_CHANNEL_REQ")

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

def hello(event, context):
    """
    A simple Lambda function that returns a greeting message.
    """
    try:
        logger.info("Hello function called")
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Hello from root!'})
        }
    except Exception as e:
        logger.error("Error in hello function: %s", str(e))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def send_telegram_message(chat_id, text):
    """
    Sends a text message to a Telegram chat.
    """
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = make_api_call(url, payload)
    return response

def send_telegram_video(chat_id, video_url):
    """
    Sends a video to a Telegram chat.
    """
    url = f"{TELEGRAM_API_URL}/sendVideo"
    payload = {
        'chat_id': chat_id,
        'video': video_url
    }
    response = make_api_call(url, payload)
    return response

def find_channel_username(channel_id):
    """
    Finds the username of a Telegram channel.
    """
    url = f"{TELEGRAM_API_URL}/getChat"
    payload = {
        'chat_id': channel_id
    }
    response = make_api_call(url, payload)
    if response is not None and response.ok:
        pprint(response.json())
        return response.json()['result']['invite_link']
    return None

def check_user_joined_channel(user_id, chat_id):
    """
    Checks if a user has joined a specific Telegram channel.
    """
    url = f"{TELEGRAM_API_URL}/getChatMember"
    payload = {
        'chat_id': telegram_channel_req,
        'user_id': user_id
    }
    response = make_api_call(url, payload)
    telegram_status = ['restricted', 'left', 'kicked']
    if response is not None and response.ok:
        if response.json()['result']['status'] in telegram_status:
            channel_username = find_channel_username(telegram_channel_req)
            send_telegram_message(user_id, f"Please join the channel (click to join: {channel_username}) to access the content.")
            return False
        else:
            return True
    else:
        send_telegram_message(chat_id, "Something went wrong. Please try again later.")
        return False

def make_api_call(url, payload):
    """
    Makes an API call to the specified URL with the given payload.
    """
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info("API call successful: %s", response.text)
        return response
    except requests.exceptions.HTTPError as http_err:
        logger.error("HTTP error occurred: %s", http_err)
    except requests.exceptions.ConnectionError as conn_err:
        logger.error("Connection error occurred: %s", conn_err)
    except requests.exceptions.Timeout as timeout_err:
        logger.error("Timeout error occurred: %s", timeout_err)
    except requests.exceptions.RequestException as req_err:
        logger.error("An error occurred: %s", req_err)
    return None

def handle_webhook(event, context):
    """
    Handles incoming webhook events from Telegram.
    """
    return asyncio.run(_handle_webhook(event, context))

async def _handle_webhook(event, context):
    """
    Asynchronous handler for processing webhook events.
    """
    try:
        if event['body'] is None:
            raise TypeError("The JSON object must be str, bytes or bytearray, not NoneType")

        update = json.loads(event['body'])
        logger.info("Update received: %s", pprint(update))

        if 'message' in update and 'chat' in update['message']:
            chat_id = update['message']['chat']['id']
            user_id = update['message']['from']['id']

            # Check if user has joined the channel
            if 'text' in update['message']:
                message_text = update['message']['text']
                if len(message_text.split(" ")) > 1:
                    if check_user_joined_channel(user_id, chat_id):
                        part = message_text.split(" ")[1]
                        part = part.replace("dot", ".")
                        response = await find_content_by_id(part, chat_id)
                        if response == 'ok':
                            return {
                                'statusCode': 200,
                                'body': 'OK'
                            }
                elif message_text == "/start":
                    send_telegram_message(chat_id, "Welcome to the bot! Please enter a number after /start")
                    return {
                        'statusCode': 200,
                        'body': 'OK'
                    }
        return {
            'statusCode': 200,
            'body': 'OK'
        }
    except TypeError as e:
        logger.error("TypeError: %s", str(e))
        return {
            'statusCode': 200,
            'body': json.dumps({'error': str(e)})
        }
    except AttributeError:
        logger.warning("Attribute Error -> Ignore")
        return {
            'statusCode': 200,
            'body': 'OK'
        }
    except Exception as e:
        logger.error("Error: %s", str(e))
        send_telegram_message(telegram_error_group, "Error: " + str(e))
        return {
            'statusCode': 200,
            'body': json.dumps({'error': str(e)})
        }
    finally:
        logging.shutdown()

async def find_content_by_id(content_id, chat_id):
    """
    Finds content by ID and sends it to the specified Telegram chat.
    """
    try:
        send_telegram_message(chat_id, "Hold on, processing your request.")
        logger.info("Processing request for content_id: %s", content_id)

        response = s3.generate_presigned_url('get_object',
                                             Params={'Bucket': bucket_name, 'Key': content_id},
                                             ExpiresIn=3600)

        try:
            # Send the video file using the generated URL
            video_response = send_telegram_video(chat_id, response)
            if video_response is None:
                send_telegram_message(chat_id, "Video not found or video removed. Please try again later.")
            else:
                logger.info("Video sent successfully")
                return 'ok'
        except requests.Timeout:
            send_telegram_message(chat_id, "The request timed out. Please try again later.")
            logger.error("TimeoutException while sending video")
    except NoCredentialsError:
        send_telegram_message(chat_id, "No Credentials Found. Please report this message to the admin.")
        logger.error("NoCredentialsError: No credentials found")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'AuthorizationQueryParametersError':
            logger.error("AuthorizationQueryParametersError: %s", e.response['Error']['Message'])
            send_telegram_message(chat_id, "Authorization error. Please try again later.")
        else:
            logger.error("ClientError: %s", e.response['Error']['Message'])
            send_telegram_message(chat_id, "Nothing found!! Try again.")
    except Exception as e:
        send_telegram_message(chat_id, "We can't process your request right now. Please try again later")
        logger.error("Exception: %s", str(e))
    finally:
        logging.shutdown()
        return {
            'statusCode': 200,
            'body': 'OK'
        }