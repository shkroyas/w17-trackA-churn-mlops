ARG BASE_IMAGE=churn-mlops:local
FROM ${BASE_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends nginx apache2-utils && rm -rf /var/lib/apt/lists/* && rm -f /etc/nginx/sites-enabled/default
COPY deploy/azure/entrypoint.py /app/deploy/azure/entrypoint.py
COPY deploy/azure/nginx.conf /etc/nginx/conf.d/default.conf
COPY deploy/azure/index.html /app/deploy/azure/index.html
ENV DEMO_TASK=A
EXPOSE 8080
CMD ["python", "/app/deploy/azure/entrypoint.py"]
