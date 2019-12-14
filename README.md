# device-simulator

## 証明書のセットアップ

ダウンロードした証明書`xxxxxxxxxx-certificate.pem.crt`を`certificate.pem`にリネームして`cert`フォルダに格納する。
ダウンロードした鍵`xxxxxxxxxx-private.pem.key`を`private.pem`にリネームして`cert`フォルダに格納する。

## cofig

`conf/setting.json`を編集する。

- "endpoint": IoT Core のエンドポイント
- "port": IoT Core のポート
- "rootCAPath": ルート証明書を格納したパス
- "certificatePath": モノの証明書を格納したパス
- "privateKeyPath": モノのプライペートキーを格納したパス
- "useWebsocket": websocket を使用するか
- "clientIdList": 任意の MQTT クライアントの名前をリストで指定
- "numOfSensors": MQTT クライアントが持つセンサーの数
- "topic": トピック
- "mode": publish／subscribe／both
- "useProxy": プロキシサーバを経由するか
- "proxyAddr": プロキシサーバのアドレス
- "proxyPort": プロキシで使用するポート
- "proxyType": for SOCKS5 proxy: proxy_type=2, for HTTP proxy: proxy_type=3

## 起動

```bash
python client.py
```
