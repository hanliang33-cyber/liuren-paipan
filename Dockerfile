FROM python:3.11-slim

WORKDIR /app

# 预装依赖（只执行一次，后续重启不重装）
RUN pip install --no-cache-dir flask ephem lunarcalendar pytz

# 复制应用代码
COPY app.py liuren_core.py ./

# 运行
EXPOSE 19130
CMD ["python", "app.py"]
