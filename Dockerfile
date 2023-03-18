FROM python:slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV VENV=/usr/src/app/.venv
ENV PATH="$VENV/bin:$PATH"

WORKDIR /usr/src/app

RUN python -m venv $VENV

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY main.py models.py ./

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]
