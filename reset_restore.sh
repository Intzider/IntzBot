sudo cp radio/streams.json radio/streams.json.bak
sudo cp .env .env.bak

git fetch &&
git reset --hard origin/main &&
sudo cp radio/streams.json.bak radio/streams.json &&
sudo cp .env.bak .env
