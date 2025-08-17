FROM python:3.10-slim
WORKDIR /app
COPY Flask_Server/ /app/Flask_Server
RUN pip install flask
# Port 5000 for flask server
EXPOSE 5000
CMD ["python", "Flask_Server/app.py"]