FROM node:22-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY ws_server.js ./
COPY public ./public
USER node
EXPOSE 9000
CMD ["node", "ws_server.js"]
