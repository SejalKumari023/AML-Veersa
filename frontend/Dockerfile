FROM node:20-alpine

WORKDIR /app

# Install dependencies for node-gyp and other build tools
RUN apk add --no-cache libc6-compat

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Run the development server
CMD ["npm", "run", "dev"]
