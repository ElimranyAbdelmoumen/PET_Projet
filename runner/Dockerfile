FROM python:3.11-slim

WORKDIR /work

# Installer R + headers pour compiler rpy2
RUN apt-get update && apt-get install -y --no-install-recommends \
    r-base \
    r-base-dev \
    && rm -rf /var/lib/apt/lists/*

# Bibliotheques Python data science + rpy2
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

# Repertoires outputs et data accessibles en ecriture
RUN mkdir -p /work/outputs /work/data && chmod 777 /work/outputs /work/data

# Copier le wrapper d'execution
COPY run_script.py /usr/local/bin/run_script.py
RUN chmod +x /usr/local/bin/run_script.py

ENTRYPOINT ["python", "/usr/local/bin/run_script.py"]
