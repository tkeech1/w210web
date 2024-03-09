FROM python:3.12.2-slim-bullseye

ARG USERNAME=python
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME && echo $USERNAME":"$USERNAME | chpasswd && adduser $USERNAME sudo

RUN apt update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata && apt-get install make wget build-essential git redis curl sudo -y && apt dist-upgrade -y && apt clean && rm -rf /var/lib/apt/lists/*

# get rid of pip warnings
RUN python3 -m pip install --upgrade pip 

USER $USERNAME

RUN mkdir /home/${USERNAME}/fastapi
COPY . /home/${USERNAME}/fastapi/
WORKDIR /home/${USERNAME}/fastapi/

RUN python3 -m pip install -r requirements.txt --user
ENV PATH="${PATH}:/home/${USERNAME}/.local/bin"

ENTRYPOINT ["uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000"]

