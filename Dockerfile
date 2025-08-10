FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8000
ENV BNX_JWT_ALGORITHM=HS256
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
