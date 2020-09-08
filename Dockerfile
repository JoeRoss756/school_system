# docker file for server
FROM ubuntu

# create directory to mount src to
RUN mkdir -p /app/src

# set working directory to application
WORKDIR /app/src

# install python3
RUN apt update
RUN apt install -y software-properties-common
RUN apt install -y python3-pip
RUN apt install -y build-essential libssl-dev libffi-dev python3-dev
RUN apt install -y wget

# install python3 packages
RUN python3 -m pip install flask
RUN python3 -m pip install pyyaml
RUN python3 -m pip install redis
RUN python3 -m pip install pymongo
RUN python3 -m pip install ipython

