# Kafka Admin Dashboard

Admin interface for managing and monitoring a distributed Kafka system.

## My Role
Developed the Kafka admin module including backend logic, UI integration, and configuration handling.

## Features
- Topic management UI
- Subscription monitoring
- Kafka configuration handling
- Flask backend service
- SQLite integration for admin data

## Tech Stack
Python, Flask, Apache Kafka, SQLite, HTML

## Files
admin_app.py – backend admin service  
config.py – Kafka configuration  
topics.html – topic management UI  
subscriptions.html – subscription monitoring UI  
project2.db – database  
requirements.txt – dependencies  

## How to Run
1. Start Kafka & Zookeeper
2. pip install -r requirements.txt
3. python admin_app.py
4. Open http://localhost:5000
