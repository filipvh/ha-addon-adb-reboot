FROM alpine:3.13

# Install ADB and Python
RUN apk add --no-cache android-tools python3 py3-pip

# Install deps
RUN pip3 install -r requirements.txt

# Copy Python script
COPY run.py /run.py

CMD [ "python3", "/run.py" ]
