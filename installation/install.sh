#!/usr/bin/env bash

if [ $# != 1 ]
then
  echo "no token provided"
  exit
fi

apt update &&
apt install git &&
apt install python3.10-venv &&
apt install ffmpeg &&

mkdir /opt/IntzBot &&
git clone https://github.com/Intzider/IntzBot.git /opt/IntzBot/ &&
sed -i "s/some_token/$1/g" /opt/IntzBot/.env &&

python3 -m venv /opt/IntzBot/discordbot &&
source /opt/IntzBot/discordbot/bin/activate &&
pip3 install -r /opt/IntzBot/requirements.txt &&
pip3 install ffmpeg-python &&
deactivate &&

cp /opt/IntzBot/installation/discordbot.service /etc/systemd/system/ &&
systemctl enable discordbot.service &&
systemctl start discordbot.service