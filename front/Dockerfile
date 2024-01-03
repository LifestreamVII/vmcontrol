# Base image
FROM node:18

# Set working directory
WORKDIR /app

# Copy package.json
COPY package.json .

# Install dependencies
RUN npm install

# Expose port
EXPOSE 3000

# Run app
CMD npm run start