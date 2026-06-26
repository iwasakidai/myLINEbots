import os
import json
import logging
import boto3
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

# ログの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# LINE SDKの設定（環境変数から取得）
configuration = Configuration(
    access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
)

# Bedrockクライアントの初期化（グローバルに置くことで実行環境を再利用）
bedrock_client = boto3.client('bedrock-runtime')

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    # Webhookのボディをパース
    body = json.loads(event.get('body', '{}'))
    events = body.get('events', [])
    
    for line_event in events:
        # メッセージイベントかつ、テキストメッセージ以外はスルー
        if line_event.get('type') != 'message' or line_event['message'].get('type') != 'text':
            continue
            
        user_message = line_event['message']['text']
        reply_token = line_event['replyToken']
        
        # 1. Bedrockを呼び出して季節の意図（Intent）を判定
        intent = detect_season_intent(user_message)
        
        # 2. 意図に応じて返信メッセージをマッピング
        if intent == "SPRING":
            reply_text = "春ですね。"
        elif intent == "SUMMER":
            reply_text = "夏ですね。"
        elif intent == "AUTUMN":
            reply_text = "秋ですね。"
        elif intent == "WINTER":
            reply_text = "冬ですね。"
        else:
            reply_text = "季節感は感じられなかったです。"
            
        # 3. LINEに返信を送信
        send_line_reply(reply_token, reply_text)
        
    return {
        'statusCode': 200,
        'body': json.dumps('OK')
    }

def detect_season_intent(user_message: str) -> str:
    """Bedrockを使ってユーザー発話から季節のインテントを抽出する"""
    
    # 使用するモデルID（コスト重視ならamazon.nova-micro-v1:0やanthropic.claude-3-haiku-...など）
    model_id = "amazon.nova-micro-v1:0"
    
    # プロンプトの組み立て
    prompt = f"""あなたはユーザーの発言から季節感を抽出するAIです。
ユーザーの発言から、春夏秋冬のいずれかの季節が感じられるかを判定し、指定された識別子のみを返してください。

識別子：
- 春を感じる場合: SPRING
- 夏を感じる場合: SUMMER
- 秋を感じる場合: AUTUMN
- 冬を感じる場合: WINTER
- 季節感を感じない場合: NONE

制約事項：
- 挨拶や余計な説明、コードブロックなどは一切出力せず、識別子の文字列（SPRING, SUMMER, AUTUMN, WINTER, NONE）のいずれか1つだけをそのまま出力してください。

ユーザーの発言：
「{user_message}」"""

    try:
        # Converse APIを使用してBedrockを呼び出し
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            inferenceConfig={
                "maxTokens": 10,     # 識別子1単語だけなので極小でOK（コスト節約）
                "temperature": 0.0   # 回答のブレをなくし固く判定させる
            }
        )
        
        # AIのテキスト出力を抽出して前後の空白を除去
        ai_output = response['output']['message']['content'][0]['text'].strip()
        logger.info(f"Bedrock Raw Output: {ai_output}")
        return ai_output
        
    except Exception as e:
        logger.error(f"Failed to call Bedrock: {e}")
        return "NONE" # エラー時は安全弁として季節感なしにする

def send_line_reply(reply_token: str, text: str):
    """LINEのReply APIを使って話しかけてきたユーザーに返信する"""
    with ApiClient(configuration) as api_client:
        api_instance = MessagingApi(api_client)
        reply_message_request = ReplyMessageRequest(
            replyToken=reply_token,
            messages=[TextMessage(text=text)]
        )
        try:
            api_instance.reply_message(reply_message_request)
            logger.info(f"Successfully sent reply: {text}")
        except Exception as e:
            logger.error(f"Failed to send LINE reply: {e}")