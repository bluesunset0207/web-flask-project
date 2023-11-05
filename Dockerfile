FROM node:18

WORKDIR /usr/src/app
COPY package*.json ./

RUN npm install -g npm

COPY . . 

EXPOSE 3000 
CMD [ "node", "app.js" ]