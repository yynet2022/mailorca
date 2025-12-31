# プログラム仕様書: MailOrca (v0.3)

## 1. 概要 (Overview)

開発環境（Django等）向けのSMTPサーバー兼Webインターフェースツール。
SMTPで受け取ったメールをメモリ上に保持し、Webブラウザから閲覧可能にする。
MailHogの軽量代替を目指し、Python単体で動作すること、設定ファイルで表示項目やネットワーク設定を柔軟に変更できることを特徴とする。

## 2. 推奨技術スタック (Tech Stack)

* **言語**: Python 3.9 以上 (必須)
* **Webフレームワーク**: `FastAPI`
* **WSGI/ASGIサーバー**: `uvicorn`
* **SMTPサーバー**: `aiosmtpd`
* **テンプレートエンジン**: `Jinja2`
* **マルチパート解析**: `python-multipart` (FastAPI フォーム/ファイル受信用)

### インストールコマンド

```bash
pip install fastapi uvicorn[standard] aiosmtpd jinja2 python-multipart
```

## 3. 設定ファイル仕様 (`config.json`)

アプリケーション起動時にカレントディレクトリの `config.json` を読み込む。存在しない場合は内部デフォルト値を使用する。

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
    "detail_headers": ["From", "To", "Cc", "Subject", "Date", "Message-ID", "X-Mailer"]
  },
  "logging": {
    "version": 1,
    "root": { "level": "WARNING" },
    "loggers": {
      "mailorca": { "level": "DEBUG" }
    }
  }
}
```

* **smtp/http host**: `0.0.0.0` 指定により外部アクセスを許可可能。
* **max_history**: 保持する最大メール数。超過時は古い順に破棄。
* **list_columns**: メール一覧画面のテーブル列。
* **detail_headers**: メール詳細画面の上部に表示するヘッダ項目。
* **logging**: 標準ライブラリ `logging.config.dictConfig` に渡されるログ設定。

## 4. 内部データ構造 (Data Structure)

オンメモリで管理するリスト（`List[Dict]`）の構造。
1メールにつき1つの辞書オブジェクトを作成する。

```python
{
    "id": "uuid-v4-string",     # URL参照用の一意なID
    "timestamp": 1704067200.0,  # 受信時刻 (float, ソート用)
    
    "raw": b"...",              # 受信した生のメールデータ (bytes, MIMEエンコードのまま)
    
    "parsed": {                 # 表示用にパース・デコード済みのデータ
        "headers": {
            "Subject": "件名テスト",            # MIMEデコード済み
            "From": "sender@example.com",
            "To": "rcpt1@ex.com, rcpt2@ex.com", # 複数宛先はカンマ区切り文字列
            "Cc": "manager@ex.com",
            "Date": "Wed, 01 Jan 2025...",
            "Received": [                       # 重複ヘッダはリストで保持
                "from mail.ex.com...",
                "from localhost..."
            ],
            "X-Custom": "Value"
        },
        "body_text": "本文テキスト...",  # text/plain (なければ None)
        "body_html": "<p>本文...</p>",   # text/html (なければ None)
    }
}
```

## 5. 機能要件 (Functional Requirements)

### 5.1 SMTP サーバー機能

* 設定されたホストとポート（デフォルト: 1025）でSMTP接続を待機する。
* 認証（Auth）は行わず、全てのメールを受け入れる。
* **受信処理フロー**:
1. データ受信。
2. `email` ライブラリを用いてパースする。
3. **ヘッダ解析**:
* MIMEエンコード（`=?utf-8?b?...?=` 等）されているヘッダはデコードして文字列化する。
* 同じヘッダ名が複数回登場した場合（`Received` 等）、リストとして値を保持する。
* 1回のみの場合は文字列として保持する。


4. **本文解析**:
* マルチパート構造を走査する。
* `text/plain` パートを抽出し、charsetに基づいてデコードして `body_text` に格納。
* `text/html` パートを抽出し、同様に `body_html` に格納。


5. 生データ(`raw`)と共にメモリ上のリストに追加する。
6. `max_history` を超えている場合、最も古いデータを削除する。



### 5.2 HTTP サーバー (Web UI) 機能

#### A. メール一覧ページ (`GET /`)

* 保存されているメールを時系列（新しい順）でテーブル表示する。
* **動的カラム生成**:
* `config.json` の `ui.list_columns` に設定されたヘッダ名を列として表示する。
* 各メールの `parsed['headers']` から該当する値を参照する。


* **行クリック遷移**:
* テーブルの各行をクリックすることで、詳細ページ (`/mail/{id}`) へ遷移する。


* **非表示**: 内部管理用IDは画面には表示しない。

#### B. メール詳細ページ (`GET /mail/{id}`)

* **ヘッダ情報エリア**:
* `config.json` の `ui.detail_headers` に定義された順序でヘッダを表示する。
* データが存在しない項目は「(empty)」と表示するか、グレーアウト表示する。
* 値がリスト（`Received` 等）の場合、改行して全て表示する。


* **本文表示エリア**:
* **タブ切り替え UI**: `[HTML]` タブと `[Plain Text]` タブを配置。
* HTMLが存在する場合、デフォルトでHTMLタブを表示。
* Plain Textのみの場合、Textタブのみ有効化。
* **HTML表示**: CSS汚染を防ぐため、`<iframe>` 内にHTMLソースを流し込む（`srcdoc` 利用など）。
* **Text表示**: `<pre>` タグ等で整形済みテキストとして表示。


* **生データダウンロード**:
* 「Download .eml」ボタンを配置。`raw` データをファイルとしてダウンロードさせる。



#### C. API エンドポイント

* `GET /api/mails`: 全メールのリストをJSON形式で返す。
* `GET /api/mails/{id}`: 特定のメールの詳細データ（`parsed` およびメタデータ）をJSONで返す。

## 6. UI デザイン方針

* Bootstrap (CDN) 等を利用し、シンプルで視認性の高いデザインにする。
* 配色はMailOrcaの名前にちなみ、白・黒・グレーを基調とする。
