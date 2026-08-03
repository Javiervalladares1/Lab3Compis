FROM ubuntu:latest

RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
