#!/bin/bash

# 데이터베이스 마이그레이션을 수행합니다.
flask db upgrade

# Flask 애플리케이션을 시작합니다.
python3 -m flask run --host=0.0.0.0