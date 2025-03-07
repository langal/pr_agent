FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install base requirements
RUN pip install --no-cache-dir -r requirements.txt

# Create script to install additional LLM providers based on environment variables
RUN echo '#!/bin/bash\n\
# Install additional LLM provider packages based on LLM_PROVIDER\n\
if [ "$LLM_PROVIDER" = "anthropic" ]; then\n\
  echo "Installing Anthropic package..."\n\
  pip install --no-cache-dir anthropic==0.8.1\n\
elif [ "$LLM_PROVIDER" = "google" ]; then\n\
  echo "Installing Google Generative AI package..."\n\
  pip install --no-cache-dir google-generativeai==0.3.1\n\
fi\n\
\n\
# Continue with the original entrypoint\n\
if [ "$DEBUG" = "1" ]; then\n\
  echo "Running in DEBUG mode. Sleeping infinity..."\n\
  exec sleep infinity\n\
else\n\
  echo "Starting PR Agent application..."\n\
  exec python app.py\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Copy application code
COPY . .

# Set environment variables
ENV PORT=5000

# No need to create the entrypoint script again as it's included in the script above

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Expose the port the app runs on
EXPOSE 5000
