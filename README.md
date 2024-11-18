# Telegram Bot with AWS Lambda and S3

This project is a Telegram bot webhook implemented using AWS Lambda and S3. The bot can send messages and videos to users from S3, check if users have joined a specific Telegram channel, and handle webhook events from Telegram.

## Bot Functionality

The bot is designed to serve content from an S3 bucket to Telegram users. When a user starts the bot using a link like `https://t.me/botusername?start=4491195549439663032dotmp4`, the bot will:

1. Extract the content ID from the URL (e.g., `4491195549439663032dotmp4`).
2. Check if the user has joined a specific Telegram channel.
3. If the user has joined the channel, find the content in the S3 bucket using the extracted ID.
4. Send the content (video) back to the user.

The purpose of this bot is to serve all content in the Telegram channel using the bot to increase the bot audience and then serve the bot as a marketing tool.

## Features

- Send text messages to Telegram users
- Send videos to Telegram users
- Check if a user has joined a specific Telegram channel
- Handle webhook events from Telegram
- Log events and errors

## Prerequisites

- AWS account
- AWS CLI configured
- Serverless Framework installed
- Telegram bot token

## Setup

1. **Clone the repository:**

    ```sh
    git clone https://github.com/your-repo/telegram-bot-lambda.git
    cd telegram-bot-lambda
    ```

2. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**

    Create a `.env` file in the root directory and add the following environment variables:

    ```env
    TELEGRAM_BOT_API=your-telegram-bot-token
    BUCKET_NAME=your-s3-bucket-name
    TELEGRAM_ERROR_GROUP=your-telegram-error-group-id
    TELEGRAM_CHANNEL_REQ=your-telegram-channel-id
    ```

4. **Deploy the application:**

    ```sh
    serverless deploy
    ```

5. **Configure the webhook in Telegram bot:**

    Replace `{bottoken}` with your actual bot token and set the webhook URL:

    ```sh
    curl -X POST "https://api.telegram.org/bot{bottoken}/setWebhook?url=https://your-api-gateway-url/webhook"
    ```

## Usage

### Sending a Text Message

To send a text message to a Telegram user, use the `send_telegram_message` function:

```python
send_telegram_message(chat_id, "Hello, this is a test message!")