# rfc-chronicle

![PyPI version](https://img.shields.io/pypi/v/rfc-chronicle.svg)
![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)
![Poetry](https://img.shields.io/badge/poetry-1.5%2B-blue.svg)
![faiss](https://img.shields.io/badge/faiss-enabled-brightgreen.svg)
![Click](https://img.shields.io/badge/click-8.1%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

## 概要：
`rfc-chronicle` は、[RFCエディター](https://www.rfc-editor.org/) に公開されているRFC（Request for Comments）情報をローカルに取り込み、検索・閲覧・エクスポートできるCLIツールです。

- RFCのメタデータ取得
- 埋め込み検索（FAISSベース）による全文検索
- レコードのピン留め・管理
- JSON / CSV / Markdown形式でのエクスポート

## 技術スタック：

![Python](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![Poetry](https://img.shields.io/badge/Poetry-1.5%2B-blue.svg)
![Click](https://img.shields.io/badge/Click-8.1%2B-purple.svg)
![Requests](https://img.shields.io/badge/Requests-2.28%2B-green.svg)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4.11%2B-yellow.svg)
![FAISS](https://img.shields.io/badge/FAISS-1.7%2B-brightgreen.svg)
![Markdown](https://img.shields.io/badge/Output-Markdown-lightgrey.svg)
![CSV](https://img.shields.io/badge/Output-CSV-orange.svg)
![JSON](https://img.shields.io/badge/Output-JSON-blueviolet.svg)

## インストール

```bash
# リポジトリをクローン
git clone https://github.com/tamai-hideyuki/rfc-chronicle.git
cd rfc-chronicle

# Poetryで依存関係をインストール
poetry install
````
---

## 使い方:


### RFCメタデータの取得

```bash
poetry run rfc show 1-9000
```

### 埋め込み検索

```bash
poetry run rfc search "検索キーワード"
```

### 詳細表示

```bash
poetry run rfc show <RFC番号> [--output json|csv|md]
```

### ピン留め管理

```bash
poetry run rfc pin add <RFC番号>
poetry run rfc pin list
poetry run rfc pin remove <RFC番号>
```

### エクスポート

```bash
poetry run rfc export --output md > rfc_list.md
```
---

## コントリビュート：

1. Issueを立てる
2. ブランチを作成 (`feat/`, `fix/` など)
3. PRを送付し、CIが通ったらマージを依頼

---

## 構成案(フルパッケージのURLからのブラウザ表示までのシーケンス図)

```mermaid
sequenceDiagram
    participant ブラウザ
    participant DNS
    participant CDN as CloudFront(CDN)
    participant S3 as S3バケット
    participant レンダラ as ブラウザレンダラ

    ブラウザ->>DNS: full-package.example.comのAレコードを照会
    DNS-->>ブラウザ: CloudFrontのエンドポイントを返却
    ブラウザ->>CDN: GET /index.html
    CDN->>S3: GET /index.html (オリジンフェッチ)
    S3-->>CDN: 200 OK + HTMLドキュメント
    CDN-->>ブラウザ: 200 OK + HTMLドキュメント

    Note over ブラウザ,レンダラ: HTMLを受信後、リソースの解析開始

    ブラウザ->>CDN: GET /styles.css
    CDN->>S3: GET /styles.css
    S3-->>CDN: 200 OK + CSS
    CDN-->>ブラウザ: 200 OK + CSS

    ブラウザ->>CDN: GET /app.js
    CDN->>S3: GET /app.js
    S3-->>CDN: 200 OK + JavaScript
    CDN-->>ブラウザ: 200 OK + JavaScript

    ブラウザ->>レンダラ: HTML/CSS/JSを渡し、レンダリング開始
    レンダラ-->>ブラウザ: ページ描画完了
```

## フルパッケージ + OIDC準拠のOAuthを組み込んだ場合のシーケン図

```mermaid
sequenceDiagram
    participant ブラウザ
    participant DNS
    participant CDN as CloudFront(CDN)
    participant S3 as S3バケット
    participant OIDC as OIDCプロバイダ
    participant TokenEP as トークンエンドポイント
    participant API as バックエンドAPI
    participant レンダラ as ブラウザレンダラ

    %% 静的資産の取得
    ブラウザ->>DNS: full-package.example.com の A レコードを照会
    DNS-->>ブラウザ: CloudFront エンドポイントを返却
    ブラウザ->>CDN: GET /index.html
    CDN->>S3: GET /index.html (オリジンフェッチ)
    S3-->>CDN: 200 OK + HTML
    CDN-->>ブラウザ: 200 OK + HTML

    Note over ブラウザ,レンダラ: HTML 受信後、JS が認証状態をチェック

    alt 未認証時
        %% 認可コードフロー開始
        ブラウザ->>OIDC: GET /authorize?response_type=code&client_id=…&redirect_uri=…
        OIDC-->>ブラウザ: 302 リダイレクト (ログインフォーム)
        ブラウザ->>OIDC: GET /login
        ブラウザ->>OIDC: POST /login (ユーザー認証)
        OIDC-->>ブラウザ: 302 リダイレクト (redirect_uri?code=…)
        ブラウザ->>CDN: GET /index.html?code=…
        CDN->>S3: GET /index.html
        S3-->>CDN: 200 OK + HTML
        CDN-->>ブラウザ: 200 OK + HTML

        %% トークン取得
        ブラウザ->>TokenEP: POST /token { grant_type=authorization_code, code, client_id, redirect_uri }
        TokenEP-->>ブラウザ: 200 OK { id_token, access_token, refresh_token }
        ブラウザ->>ブラウザ: localStorage にトークンを保存
    end

    %% 保護されたリソースの取得
    ブラウザ->>API: GET /protected-data (Authorization: Bearer access_token)
    API-->>ブラウザ: 200 OK + JSON データ

    %% 最終レンダリング
    ブラウザ->>レンダラ: HTML/CSS/JS + データ を渡して描画
    レンダラ-->>ブラウザ: ページ描画完了
```

## フルパッケージ + ログインしてるユーザーID取得のシーケンス図

```mermaid
sequenceDiagram
    participant ブラウザ
    participant UserInfoEP as OIDCプロバイダ\nUserInfoエンドポイント
    participant API as バックエンドAPI
    participant レンダラ as ブラウザレンダラ

    Note over ブラウザ: 認可コードフロー完了後、トークンを保持

    ブラウザ->>UserInfoEP: GET /userinfo\n(Authorization: Bearer access_token)
    UserInfoEP-->>ブラウザ: 200 OK { "sub": "ユーザーID", "name": "...", ... }
    ブラウザ->>ブラウザ: ローカルでユーザーID抽出・格納

    Note over ブラウザ: ログイン中ユーザーIDを取得

    ブラウザ->>API: GET /protected-data\n(Authorization: Bearer access_token)
    API-->>ブラウザ: 200 OK + JSONデータ

    ブラウザ->>レンダラ: HTML/CSS/JS + データ + ユーザーID を渡して描画
    レンダラ-->>ブラウザ: ページ描画完了
```
