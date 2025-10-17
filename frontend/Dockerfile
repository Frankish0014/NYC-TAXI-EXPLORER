FROM nginx:alpine

# Remove default html
RUN rm -rf /usr/share/nginx/html/*

# Copy frontend code
COPY . /usr/share/nginx/html

# Expose port
EXPOSE 80
