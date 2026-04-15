FROM python:3.11-slim

RUN useradd -m -u 10001 runner

WORKDIR /work

# Installer R + headers pour compiler rpy2
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Bibliothèques Python courantes pour data science + rpy2
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    scikit-learn \
    scipy \
    seaborn \
    requests \
    openpyxl \
    xlrd \
    rpy2

# Copier le wrapper d'exécution
COPY run_script.py /usr/local/bin/run_script.py
RUN chmod +x /usr/local/bin/run_script.py

USER runner

ENTRYPOINT ["python", "/usr/local/bin/run_script.py"]