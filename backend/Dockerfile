FROM python:3.7.11-slim

WORKDIR /usr/src/crowdplay

RUN apt-get update

# We're gonna installed a package from a private repo => git & openssh-client
# unrar-free is needed for AutoROM
RUN apt-get install \
    ffmpeg \
    libsm6 \
    libxext6  \
    git \
    openssh-client \
    software-properties-common \
    -y

RUN apt-add-repository non-free
RUN apt-get update

# Needed for Pendulum environment
RUN apt-get install python3-opengl xvfb -y


# If your installation depends on an additional private repository, you can use these lines to add a github deploy key
# RUN mkdir -p /root/.ssh
# COPY ssh /root/.ssh
# RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
# RUN chmod 0600 /root/.ssh/secret_key

COPY requirements.txt .
RUN pip install --disable-pip-version-check -r requirements.txt

# DO NOT USE AutoROM, or it will download ROMs every time you build the container.
# Copy them from repository.
RUN mkdir /usr/local/lib/python3.7/site-packages/multi_agent_ale_py/roms/
COPY ROM /usr/local/lib/python3.7/site-packages/multi_agent_ale_py/roms/

RUN ale-import-roms /usr/local/lib/python3.7/site-packages/multi_agent_ale_py/roms/

COPY . .
ENV DISPLAY=:0
CMD DISPLAY=:0 xvfb-run -n0 python -m crowdplay_backend
