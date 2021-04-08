##FROM openjdk:11-buster
FROM ubuntu:bionic

USER root
WORKDIR /root

SHELL [ "/bin/bash", "-c" ]

ARG PYTHON_VERSION_TAG=3.8.3
ARG LINK_PYTHON_TO_PYTHON3=1

RUN apt-get -qq -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get -qq -y install \
        gcc \
        g++ \
        zlibc \
        zlib1g-dev \
        libssl-dev \
        libbz2-dev \
        libncurses5-dev \
        libgdbm-dev \
        libgdbm-compat-dev \
        liblzma-dev \
        libreadline-dev \
        uuid-dev \
        libffi-dev \
        tk-dev \
        wget \
        curl \
        git \
        make \
        sudo \
        bash-completion \
        tree \
        vim \
        software-properties-common 

RUN apt-get -qq -y update && \
    DEBIAN_FRONTEND=noninteractive apt-get -qq -y install \
        cmake
RUN DEBIAN_FRONTEND=noninteractive apt-get -qq -y install default-jre python3.8 python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install numpy
RUN pip3 install Cython
RUN pip3 install blis
RUN pip3 install spacy
RUN pip3 install arabic_reshaper

# Create user with sudo powers
RUN useradd -m taskquerybuilder && \
    usermod -aG sudo taskquerybuilder && \
    echo '%sudo ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers && \
    cp /root/.bashrc /home/taskquerybuilder/ && \
    chown -R --from=root taskquerybuilder /home/taskquerybuilder

# Use C.UTF-8 locale to avoid issues with ASCII encoding
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ENV HOME /home/taskquerybuilder
ENV USER taskquerybuilder
USER taskquerybuilder

# Avoid first use of sudo warning. c.f. https://askubuntu.com/a/22614/781671
RUN touch $HOME/.sudo_as_admin_successful

# The following put files in user's home directory
RUN LC_ALL=C.UTF-8 LANG=C.UTF-8 python3 -m spacy download en_core_web_sm

WORKDIR /home/taskquerybuilder
ADD . .
RUN sudo chown -R taskquerybuilder .
