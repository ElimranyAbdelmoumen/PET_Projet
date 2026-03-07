FROM python:3.11-slim

RUN useradd -m -u 10001 runner

WORKDIR /work

# Bibliothèques Python courantes pour data science
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    matplotlib \
    scikit-learn \
    scipy \
    seaborn \
    requests \
    openpyxl \
    xlrd

# Copier le wrapper d'exécution
COPY run_script.py /usr/local/bin/run_script.py
RUN chmod +x /usr/local/bin/run_script.py

USER runner

ENTRYPOINT ["python", "/usr/local/bin/run_script.py"]