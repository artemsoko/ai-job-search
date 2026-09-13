FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.11-slim
RUN useradd --create-home --uid 1000 app
COPY --from=builder /install /usr/local
USER app
ENTRYPOINT ["game"]
