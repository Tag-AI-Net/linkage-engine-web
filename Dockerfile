# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy your frontend code into the container
COPY . /app

# Install Streamlit and dependencies
RUN pip install --no-cache-dir streamlit pandas requests

# Expose the port Cloud Run expects
EXPOSE 8080

# Configure Streamlit to run on the correct port and allow large uploads (5GB)
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_MAX_UPLOAD_SIZE=5000
ENV STREAMLIT_SERVER_ENABLE_CORS=false

# Command to run the app
CMD ["streamlit", "run", "app.py"]
