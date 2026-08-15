# ==============================================================================
# Stage 1: Build React Production Bundle
# ==============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Install build dependencies
COPY package*.json ./
RUN npm ci

# Copy frontend source files
COPY . .

# Pass API base URL build argument (defaults to relative /api for reverse proxy)
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Build optimized production bundle
RUN npm run build

# ==============================================================================
# Stage 2: Production Nginx Server
# ==============================================================================
FROM nginx:alpine

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose standard HTTP port
EXPOSE 80

# Run Nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
