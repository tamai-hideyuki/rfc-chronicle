FROM nginx:alpine

# HTML やアセットを配置
COPY web-ui/ /usr/share/nginx/html
# カスタム Nginx 設定を上書き
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
