import requests
import json
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import openai
import random

#IEEEのapiキー
IEEE_API_KEY = 'IEEEのapiキー'
# IEEE APIのエンドポイント
base_url = 'http://ieeexploreapi.ieee.org/api/v1/search/articles'
#OpenAIのapiキー
openai.api_key = 'OpenAIのAPIキー'
# Slack APIトークン
SLACK_API_TOKEN = 'SlackbotのAPIトークン'
# Slackに投稿するチャンネル名を指定する
SLACK_CHANNEL = "#general"

def get_summary(result):
    system = """与えられた論文の要点を3点のみでまとめ、以下のフォーマットで日本語で出力してください。```
    タイトルの日本語訳
    ・要点1
    ・要点2
    ・要点3
    ```"""

    text = f"title: {result['title']}\nbody: {result['abstract']}"
    response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': text}
                ],
                temperature=0.25,
            )
    summary = response['choices'][0]['message']['content']
    title_en = result['title']
    title, *body = summary.split('\n')
    body = '\n'.join(body)
    date_str = result['publication_date']
    message = f"発行日: {date_str}\n{result['pdf_url']}\n{title_en}\n{title}\n{body}\n"

    return message


# Slack APIクライアントを初期化する
client = WebClient(token=SLACK_API_TOKEN)
#queryを用意
query = 'deep learning'

# クエリパラメータを指定してAPIを呼び出す,max_recordsは任意
params = {
    'apikey': IEEE_API_KEY,
    'format': 'json',
    'max_records': 20,
    'start_record': 1,
    'sort_order': 'asc',
    'sort_field': 'article_number',
    'abstract': query
}

response = requests.get(base_url, params=params)

if response.status_code == 200:
    print("API call successful")
else:
    print("API call unsuccessful with status code:", response.status_code)

# APIからのレスポンスをJSON形式で取得
result = json.loads(response.text)

#ランダムにnum_papersの数だけ選ぶ
num_papers = 3
results = random.sample(result['articles'], k=num_papers)

# 論文情報をSlackに投稿する
for i,result in enumerate(results):
    try:
        # Slackに投稿するメッセージを組み立てる
        message = "今日の論文です！ " + str(i+1) + "本目\n" + get_summary(result)
        # Slackにメッセージを投稿する
        response = client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text=message
        )
        print(f"Message posted: {response['ts']}")
    except SlackApiError as e:
        print(f"Error posting message: {e}")