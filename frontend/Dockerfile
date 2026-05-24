FROM node:20-alpine AS builder

WORKDIR /app

# 安装依赖
COPY package.json ./
RUN npm install

# 复制源代码
COPY . .

# 构建
RUN npm run build

# 生产镜像
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
