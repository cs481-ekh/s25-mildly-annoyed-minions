# Use Ubuntu 22.04 as the base image
FROM ubuntu:latest

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive
ENV VIRTUAL_ENV=/app/.env

# Install system dependencies
RUN apt update -y && apt install -y \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    curl \
    git \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    python3.12 \
    python3.12-venv \
    python3-pip \
    python3.12-tk \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    tesseract-ocr-eng \
    libtiff6 \
    libgl1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

RUN python -m venv $VIRTUAL_ENV
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

# Add tesseract English traineddata manually
RUN wget https://github.com/tesseract-ocr/tessdata/raw/refs/heads/main/eng.traineddata && \
    mv eng.traineddata /usr/share/tesseract-ocr/5/tessdata/eng.traineddata

# Set working directory
WORKDIR /app

COPY requirements.txt . 

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Set the entrypoint
RUN chmod +x entrypoint.sh
CMD ["/app/entrypoint.sh"]
