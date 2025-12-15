# Frontend Dockerfile for React + tldraw app
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (for better caching)
COPY frontend/package*.json ./

RUN npm install

# Copy the rest of the frontend code
COPY frontend/ ./

# Expose port 5173 (Vite default)
EXPOSE 5173

# Start the development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
