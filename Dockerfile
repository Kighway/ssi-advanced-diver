FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements-lock.txt ./
RUN python -m pip install --no-cache-dir -r requirements-lock.txt

COPY . ./
# A failing geometry or UI regression prevents a release.
RUN python -m pytest -q && useradd --create-home --uid 10001 compass

USER compass
EXPOSE 8501
CMD ["sh", "scripts/start.sh"]
