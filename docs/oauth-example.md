**使用例**

## 各プロバイダ（Google／Apple／Yahoo! JAPAN／Facebook／Alipay）のOAuth認証フローから“サイト側でユーザーIDを取得するまで”を正しく把握する

### 1. 「OAuth 2.0／OpenID Connect」のリファレンス RFC を収集

- 各社はベースとして OAuth 2.0（RFC 6749）や OpenID Connect（OIDC）を使っています。
- まずはこれらの公式仕様をローカルに落として、全文検索／意味検索できるようにします。
```bash
# CLI で見るだけなら
# OAuth 2.0 Core
poetry run rfc-chronicle show 6749 --output md
# Bearer トークン
poetry run rfc-chronicle show 6750 --output md
# OAuth 2.0 Authorization Server Metadata (メタデータエンドポイント)
poetry run rfc-chronicle show 8414 --output md
# OpenID Connect Core（OpenID Foundation が管理していますが、関連するRFCもいくつか）
poetry run rfc-chronicle show 7519 --output md    # JSON Web Token (JWT)
poetry run rfc-chronicle show 7662 --output md    # Token Introspection

```

### 2. rfc-chronicle で「認可エンドポイント／トークンエンドポイント／IDトークン」などを全文検索・意味検索(各仕様書の該当セクションをすばやく参照するため)

```bash
# 「authorization code grant」フローの概要を全文から探す
poetry run rfc-chronicle fulltext "authorization code"

# ID トークンの定義（sub クレームなど）を
poetry run rfc-chronicle fulltext "ID Token"

# 「user identifier」「subject」「sub claim」などで意味検索
poetry run rfc-chronicle fulltext "sub claim user identifier"

poetry run rfc-chronicle fulltext "OAuth 2.0"

poetry run rfc-chronicle fulltext "authorization code grant"

poetry run rfc-chronicle fulltext "OpenID Connect"

poetry run rfc-chronicle fulltext "JSON Web Token"

poetry run rfc-chronicle fulltext "OAuth OIDC"

# 検索後、タイトルだけ知りたい時など
poetry run rfc-chronicle show <RFC番号> | head -n <確認したい行数>
```

### 3. セマンティックサーチで意味検索
**semsearch は「入力クエリ文字列をベクトル化→コレクション内のドキュメントと距離計算→上位 k 件を返す」という仕組み**
**なので、RFC 名称や技術用語として共通度が高い語句を与えるのがコツ**
```bash
poetry run rfc-chronicle semsearch "OAuth 2.0"

poetry run rfc-chronicle semsearch "authorization code grant"

poetry run rfc-chronicle semsearch "OpenID Connect"

poetry run rfc-chronicle semsearch "JSON Web Token"

# 検索後、タイトルだけ知りたい時など
poetry run rfc-chronicle show <RFC番号> | head -n <確認したい行数>
```


### 5. 各プロバイダ固有のドキュメントを並行して参照
**RFC はあくまで標準仕様なので、Google や Facebook、Alipay といったサービスごとに「どのエンドポイントを叩くと、どんなクレーム（sub, email, user_id）を含んだレスポンスが返ってくるか」はベンダー独自**

#### Google: https://developers.google.com/identity/protocols/oauth2?hl=ja

#### Apple (Sign in with Apple)
- Sign in with Apple - Apple Developer Documentation: https://developer.apple.com/jp/sign-in-with-apple/
- Implement User Authentication with Sign in with Apple: https://developer.apple.com/jp/documentation/authenticationservices/implementing_user_authentication_with_sign_in_with_apple/

#### Yahoo! JAPAN (Yahoo! ID連携)
- Yahoo! ID連携とは: https://developer.yahoo.co.jp/yconnect/v2/introduction.html
- Authorization Codeフロー - Yahoo!デベロッパーネットワーク: https://developer.yahoo.co.jp/yconnect/v2/authorization_code/

#### Facebook (Facebookログイン)
- Facebookログイン - Meta for Developers: https://developers.facebook.com/docs/facebook-login/
- ウェブ向けFacebookログインを実装する: https://developers.facebook.com/docs/facebook-login/web

#### Alipay
- alipay.system.oauth.token | Global API - Antom docs (旧Alipay Global): https://docs.antom.com/ac/global/oauth_token

---