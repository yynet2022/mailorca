# MailOrca 🐋

MailOrca は、開発環境向けの軽量な SMTP サーバー兼 Web インターフェースツールです。
MailHog のようなツールを Python エコシステムだけで完結させたい開発者のために作られました。
Django や Flask などの Web アプリケーション開発時に、ローカルでメール送信テストを行うのに最適です。

## 特徴

*   **Python Native**: Python 3.9+ だけで動作します。Go や Docker がない環境でも `pip` だけで導入可能です。
*   **Web UI**: 受信したメールをブラウザで即座に確認できます。HTML/Text パートの切り替えや、生の `.eml` ダウンロードも可能です。
*   **Simple SMTP Server**: `aiosmtpd` をベースにした非同期 SMTP サーバーが、アプリケーションからのメールを受け取ります。
*   **Configurable**: ポート番号や表示項目は `config.json` で柔軟に設定可能です。
*   **REST API**: メールデータにアクセスするための JSON API も提供しています。

## 動作要件

*   Python 3.9 以上

## インストール

1.  リポジトリをクローンします。
    ```bash
    git clone https://github.com/yynet2022/mailorca.git
    cd mailorca
    ```

2.  依存パッケージをインストールします。
    ```bash
    pip install -r requirements.txt
    ```

## 使い方

### 起動

以下のコマンドでサーバーを起動します。

```bash
python runserver.py
```

コマンドライン引数や環境変数で設定を上書きすることも可能です。

```bash
# ヘルプを表示
python runserver.py --help

# ポート番号を変更して起動する例
python runserver.py --smtp-port 2025 --http-port 8080

# 詳細なログを出力して起動 (-v 1: INFO, -v 2: DEBUG)
python runserver.py -v 2
```

#### 環境変数による設定

引数の代わりに環境変数で設定することも可能です（プレフィックス `MAILORCA_` を使用）。

*   `MAILORCA_SMTP_PORT=2025`
*   `MAILORCA_HTTP_PORT=8080`

デフォルトでは以下のポートで待機します。

*   **SMTP Server**: `127.0.0.1:1025`
    *   開発中のアプリケーションのメール送信設定（Host/Port）をここに合わせます。
*   **Web UI**: `http://127.0.0.1:8025`
    *   ブラウザでアクセスして受信メールを確認します。

### 設定

`config.json` を編集することで設定を変更できます。

```json
{
  "smtp": {
    "host": "127.0.0.1",
    "port": 1025
  },
  "http": {
    "host": "127.0.0.1",
    "port": 8025
  },
  "max_history": 100,
  "ui": {
    "list_columns": ["Date", "Subject", "To", "From"],
    "detail_headers": ["From", "To", "Cc", "Subject", "Date", "Message-ID"]
  }
}
```

*   `smtp`, `http`: ホストとポートを指定します。外部からアクセスさせる場合は `"0.0.0.0"` を指定してください。
*   `max_history`: メモリ上に保持するメールの最大件数です。これを超えると古いものから削除されます。
*   `ui`: Web UI の一覧や詳細画面に表示するヘッダー項目をカスタマイズできます。

## ライセンス

本ソフトウェアは [MIT License](LICENSE) の下で公開されています。
