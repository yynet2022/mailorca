"""設定 (CONFIG) 橋渡し用

    uvicorn.run(...) するスクリプトファイルと
    app = FastAPI(...) するスクリプトファイルは分ける必要がある。
    でないと、
     1. click を使ったコマンド引数の解釈
     2. 設定ファイル読み込み
     3. app の生成
    この順序がうまく制御できない。

    app は、そのファイル内でグローバルな変数にしたいが、
    click からの引数の解釈は、基本的に関数内で処理をする必要がある。

    もちろん click じゃなく argparse を使うとか、
    reload 捨てて uvicorn.run(app, ...) のようにオブジェクトを直接渡すとか、
    click の standalone_mode を False にするとか、
    やってやれないことはないけど、
    今回は uvicorn に合わせて click 使ってみたいし、
    トリッキーな方法は、美しくないからしない。

    そして上記二つを分けるなら、設定の橋渡し役が必要になる。
    それが、このファイルの役目。

"""
import json

CONFIG = {
    "smtp": {"host": "127.0.0.1", "port": 1025},
    "http": {"host": "127.0.0.1", "port": 8025},
    "max_history": 100,
    "ui": {
        "list_columns": ["Date", "Subject", "To", "From"],
        "detail_headers": ["From", "To", "Cc", "Subject", "Date"]
    },
    "logging": {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s %(name)s:%(lineno)s %(funcName)s:%(levelname)s: %(message)s'  # noqa: E501
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'simple',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
        'loggers': {
            'mailorca': {
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }
}


def load_config(config_file):
    """ Configuration Loading """
    c = CONFIG
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            u = json.load(f)
        # Merge with defaults
        c['smtp'] = c['smtp'] | u.get('smtp', {})
        c['http'] = c['http'] | u.get('http', {})
        c['max_history'] = u.get('max_history', c['max_history'])
        c['ui']['list_columns'] = u.get('ui', {}).get(
            'list_columns', c['ui']['list_columns'])
        c['ui']['detail_headers'] = u.get('ui', {}).get(
            'detail_headers', c['ui']['detail_headers'])
        c['logging'] = u.get('logging', c['logging'])
    except Exception as e:
        print(f"Config file: {e}")
        print("Using defaults.")
