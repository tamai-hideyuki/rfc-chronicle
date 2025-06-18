## M8: HTTPベース Web UI

以下の構成・機能が実装・動作します。

### ✔︎ シンプル HTTP Web UI 骨格構築
- `web-ui/` ディレクトリに静的ファイルを配置
    - `index.html`（CLI API 呼び出し用の `fetch` 実装）
    - `manifest.json` とアイコン 192×192, 512×512

### ✔︎ CLI バックエンド API 連携
- `<script>` 内で `fetch('/api/metadata')` 等を実行
- 取得データを `<div id="app">` へ整形表示

### ✔︎ 環境準備不要・即起動
- HTTPS／CA 証明書不要、`http-server` などのシンプルな HTTP サーバで動作
- Chrome DevTools（Network / Console）でエラー無し

---
 
既存 CLI 機能を迅速にブラウザ上で可視化できる基盤が整いました。  

```mermaid
sequenceDiagram
  participant Browser as ブラウザ
  participant Proxy as Nginxプロキシ
  participant Front as Frontendコンテナ
  participant Back as Backendコンテナ

  Browser->>Proxy: GET /
  Proxy->>Front: GET / (静的HTML)
  Front-->>Proxy: HTML/CSS/JS
  Proxy-->>Browser: レスポンス

  Browser->>Proxy: GET /api/metadata
  Proxy->>Back: GET /api/metadata
  Back-->>Proxy: JSONメタデータ
  Proxy-->>Browser: JSONメタデータ

  Browser->>Proxy: GET /api/search?q=xxx
  Proxy->>Back: GET /api/search?q=xxx
  Back-->>Proxy: JSON検索結果
  Proxy-->>Browser: JSON検索結果

  Browser->>Proxy: POST /api/pin/1
  Proxy->>Back: POST /api/pin/1
  Back-->>Proxy: {status: "ok"}
  Proxy-->>Browser: {status: "ok"}
```