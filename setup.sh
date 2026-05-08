#!/bin/bash
pkg update -y
pkg install -y python python-pip termux-api
pip install flask flask-cors groq python-dotenv
echo "GROQ_API_KEY=your_key_here" > .env
echo "USER_NAME=Sir" >> .env
echo "PORT=8080" >> .env
mkdir -p templates
echo "Setup done!"
