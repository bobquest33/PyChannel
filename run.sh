#!/usr/bin/env bash

FLASK_BOARD_CONFIG=$1 gunicorn PyChannel:app
