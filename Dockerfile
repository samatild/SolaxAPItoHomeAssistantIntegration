FROM python:3-slim

RUN mkdir -p /var/www/solax /var/log

# Dependencies
RUN pip install requests

# Prepare
COPY solaxmonitor.py /app/solaxmonitor.py
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh
EXPOSE 8080

# Start
CMD ["/app/start.sh"]