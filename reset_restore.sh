sudo cp radio/streams.json radio/streams.json.bak
sudo cp .env .env.bak

git fetch &&
git reset --hard origin/main &&
sudo cp streams.json.bak streams.json &&
sudo cp .env.bak .env
