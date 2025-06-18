# Nginx を使って静的ファイルを配信
FROM nginx:alpine

# プロジェクトルートから web-ui ディレクトリをコピー
COPY web-ui /usr/share/nginx/html

# ポート 80 を expose
EXPOSE 80

# Nginx をフォアグラウンドで起動
CMD ["nginx", "-g", "daemon off;"]
