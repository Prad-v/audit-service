# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Install all dependencies (including dev dependencies for build)
RUN npm ci

# Copy source code
COPY src ./src
COPY index.html ./

# Build the application with environment variable
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npx vite build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Remove default nginx configuration
RUN rm -f /etc/nginx/conf.d/default.conf

# Copy documentation
COPY docs /usr/share/nginx/docs

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]