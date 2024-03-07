FROM python:3.12.2-slim-bullseye

ARG USERNAME=python
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && echo $USERNAME":"$USERNAME | chpasswd && adduser $USERNAME sudo \
    # the following two lines are for VS Code devcontainers
    && mkdir -p /home/$USERNAME/.vscode-server /home/$USERNAME/.vscode-server-insiders \
    && chown ${USER_UID}:${USER_GID} /home/$USERNAME/.vscode-server*

RUN apt update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata && apt-get install make wget build-essential git redis curl sudo -y && apt dist-upgrade -y && apt clean && rm -rf /var/lib/apt/lists/*

# get rid of pip warnings
RUN python3 -m pip install --upgrade pip 
#RUN curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

USER $USERNAME
ENV PATH="${PATH}:/home/${USERNAME}/.local/bin"

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt --user


