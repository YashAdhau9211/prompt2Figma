FROM python:3.9-slim

# Install Node.js
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend files
COPY prompt2Figma-Backend/requirements.txt ./
COPY prompt2Figma-Backend/package*.json ./

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN npm install

# Copy the rest of the backend code
COPY prompt2Figma-Backend/ ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
