# Image de développement : sert l'application via le serveur de dev Vite (hot reload).
# Pour une mise en production, utiliser `npm run build` et servir /dist avec nginx.
FROM node:20-alpine

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev"]
