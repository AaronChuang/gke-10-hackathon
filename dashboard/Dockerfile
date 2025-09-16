# 多階段建置：第一階段 - 建置 Vue 應用
FROM node:20-alpine AS builder

# 啟用 corepack 並安裝 pnpm
RUN corepack enable
RUN corepack prepare pnpm@latest --activate

WORKDIR /app

# 複製 package 檔案和 pnpm 配置
COPY package.json pnpm-lock.yaml* ./
COPY tsconfig*.json ./
COPY vite.config.ts ./

# 安裝依賴
RUN pnpm install

# 複製源碼
COPY src/ ./src/
COPY index.html ./

# 建置應用
RUN pnpm run build

# 第二階段 - 提供靜態檔案
FROM nginx:alpine

# 複製建置結果到 nginx
COPY --from=builder /app/dist /usr/share/nginx/html/

# 複製 nginx 配置（如果需要）
# COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
