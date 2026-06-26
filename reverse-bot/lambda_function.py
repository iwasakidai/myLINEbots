import os
import json
import logging

# LINE Bot SDK v3 のインポート
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent

# ログの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 環境変数から LINE の認証情報を取得
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

def lambda_handler(event, context):
    # API Gateway から渡されるヘッダーから署名を取得
    headers = event.get('headers', {})
    signature = headers.get('x-line-signature') or headers.get('X-Line-Signature')
    
    # LINE から送られてきた body（リクエストボディ）
    body = event.get('body', '')
    
    # 署名がない場合はエラー
    if not signature:
        logger.error("Missing signature")
        return {'statusCode': 400, 'body': 'Missing signature'}

    try:
        # 署名検証とイベントのハンドリング
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature. Please check channel secret.")
        return {'statusCode': 400, 'body': 'Invalid signature'}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {'statusCode': 500, 'body': 'Internal Server Error'}

    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }

# テキストメッセージを受信したときの処理
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    # 1. ユーザーが送信したテキストを取得
    user_message = event.message.text
    
    # 2. 【ここが肝】スライスを使って文字列をひっくり返す（「とり」→「りと」）
    reversed_message = user_message[::-1]
    
    # 3. 返信メッセージの送信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reversed_message)]
            )
        )