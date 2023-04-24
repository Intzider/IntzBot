#!/usr/bin/env bash

if [[ $(basename $0) == 'reset_restore.sh' ]]
then
  echo "wat dis"
  cp "./reset_restore.sh" "../reset.sh"
  chmod +x ../reset.sh
  ../reset.sh
  exit
fi

sudo cp radio/streams.json radio/streams.json.bak &&
sudo cp .env .env.bak

git fetch &&
git reset --hard origin/main &&
sudo cp radio/streams.json.bak radio/streams.json &&
sudo cp .env.bak .env &&
sudo systemctl restart discordbot.service