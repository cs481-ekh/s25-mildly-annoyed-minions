# R&D Labs Directories Parser

![Clean, Build, & Test](https://github.com/cs481-ekh/s25-mildly-annoyed-minions/actions/workflows/clean-build-test.yml/badge.svg)

Boise State University CS 481 - Senior Design Project

Team Members:

- Dylan Gresham
- Carson Keller
- Josh Miller

## Development Setup

Assuming machine is running Ubuntu and Python 3.12 is already installed on your machine.

```bash
sudo apt update -y; sudo apt install -y build-essential libssl-dev zlib1g-dev \
          libbz2-dev libreadline-dev libsqlite3-dev curl git \
          libncursesw5-dev xz-utils tk-dev python3.12-tk libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev \
          tesseract-ocr libtesseract-dev poppler-utils tesseract-ocr-eng libtiff6

wget https://github.com/tesseract-ocr/tessdata/raw/refs/heads/main/eng.traineddata

sudo mv eng.traineddata /usr/share/tesseract-ocr/5/tessdata/eng.traineddata

python -m venv .env

source .env/bin/activate

pip install -r requirements.txt
```

