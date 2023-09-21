#!/bin/sh
supervisord -c supervisord.conf

python app.py
