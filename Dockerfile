# Use an Ubuntu-based image
FROM ubuntu:20.04

# Install cron and other necessary packages
RUN apt-get update && apt-get install -y \
    cron \
    python3 \
    python3-pip \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    postgresql-client

# Set environment variables (optional but recommended)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Copy the Django project files into the container
COPY . /app/

# Set environment variables with default values (users can override these at runtime)
ENV BASE_URL='http://127.0.0.1:800/'
ENV REGION_NAME='ap-south-1'
ENV BUCKET_NAME='audible-bucket'
ENV CATEGORIES_REFRESH_TIME_IN_MIN=1440
ENV BATCH_TIME='0 0 * * *'
ENV BATCH_LOCALE='us,in'

# Make the script executable
RUN chmod +x /app/cronjob.sh

# Add a cron job that runs the script at the specified time
RUN crontab -l | { cat; echo "$BATCH_TIME /app/cronjob.sh"; } | crontab -

# Expose the port that the Django development server will use (default is 8000)
EXPOSE 8000

# Run the Django development server
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
