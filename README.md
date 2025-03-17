# このプロジェクトについて
- オンライン上の政策熟議PFを構築する「いどばた」PJのリポジトリです。
    - PJ全体の意義・意図は[こちらのスライド](https://docs.google.com/presentation/d/1etZjpfj9v59NW5REC4bOv4QwVq_ApZMFDMQZqPDHb8Q/edit#slide=id.g339b8863127_0_989)のP20からP50を参照ください。
- 本PJは、以下に示す複数のモジュールで構築されています
    - [idobata-agent](https://github.com/takahiroanno2024/idobata-agent/) (フォーラムの投稿に反応し、モデレーションを行うモジュール)
    - [idobata-analyst](https://github.com/takahiroanno2024/idobata-analyst/)（フォーラムやSNSの投稿を分析し、レポートを作成するモジュール）
    - [idobata-infra](https://github.com/takahiroanno2024/idobata-infra/)（フォーラムのインフラを構築する設定）
    - [idobata-sns-agent](https://github.com/takahiroanno2024/idobata-sns-agent/)（SNSの投稿を収集したり、投稿を行うためのモジュール）

# 開発への参加方法について

- 本PJは、開発者の方からのコントリビュートを募集しています！ぜひ一緒に日本のデジタル民主主義を前に進めましょう！
- プロジェクトのタスクは[GitHub Project](https://github.com/orgs/takahiroanno2024/projects/4)で管理されています。
    - [good first issueタグ](https://github.com/orgs/takahiroanno2024/projects/4/views/1?filterQuery=good+first+issue)がついたIssueは特に取り組みやすくなっています！
- プロジェクトについてのやりとりは、原則[デジタル民主主義2030のSlackの「開発_いどばた」チャンネル](https://w1740803485-clv347541.slack.com/archives/C08FF5MM59C)までお願いします
- コントリビュートにあたっては、本リポジトリのrootディレクトリにあるCLA.md（コントリビューターライセンス）へ同意が必要です。
    - 同意する手順は、Pull Requestのテンプレートに記載があります

# 本PJの開発者向け情報

This bot monitors Twitter for mentions or replies to specific tweets and automatically responds using OpenAI's GPT model.

## Features

- OAuth 2.0 authentication with Twitter API
- Automatic token refresh
- Monitoring for mentions and replies to specific tweets
- AI-powered responses using OpenAI's GPT model
- Environment variable configuration

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in your credentials:
   ```
   cp .env.example .env
   ```
4. Edit the `.env` file with your:
   - Twitter API credentials (Client ID, Client Secret, Redirect URI)
   - OpenAI API key
   - Target username to monitor

## Twitter API Setup

1. Create a Twitter Developer account at https://developer.twitter.com/
2. Create a project and app
3. Configure your app with OAuth 2.0 and the following permissions:
   - Read and Write permissions
   - Type of App: Web App, Automated App or Bot
4. Set your Redirect URI (e.g., https://localhost:3000/callback)
5. Copy your Client ID and Client Secret to the `.env` file

## Usage

1. (Optional) Edit `target_tweet_ids.txt` to add specific tweet IDs you want to monitor for replies
2. Run the bot:
   ```
   python main.py
   ```
3. On first run, you'll be prompted to authenticate with Twitter:
   - Open the provided URL in your browser
   - Authorize the application
   - Copy the redirected URL and paste it back into the terminal

The bot will now continuously monitor Twitter and respond to mentions and replies.

## Configuration

- `TARGET_USERNAME`: Twitter username to monitor for mentions (without @)
- `target_tweet_ids.txt`: List of tweet IDs to monitor for replies (one per line)
- `POLLING_INTERVAL_SECONDS`: How often to check for new tweets (default: 600 seconds / 10 minutes)
- `SEARCH_WINDOW_MINUTES`: How far back to search for tweets (default: 10 minutes)

## Files

- `main.py`: Entry point for the application
- `config.py`: Configuration loading from environment variables
- `twitter/`: Twitter API integration
  - `auth.py`: Authentication with Twitter API
  - `api.py`: Twitter API operations
- `openai_client/`: OpenAI integration
  - `api.py`: OpenAI API operations
- `utils/`: Utility functions
  - `file_utils.py`: File operations

## License

See the LICENSE file for details.
