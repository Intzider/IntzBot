import asyncio
from datetime import datetime
from time import time
import json
import logging
import os
from urllib.request import urlopen
from .playing import playing, channels

import discord
from discord import FFmpegOpusAudio, app_commands, Interaction
from discord.ext import commands
from shazamio import Shazam

STREAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams.json")

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)


def get_streams() -> dict:
    with open(STREAMS, "r") as file:
        return json.load(file)


class RadioCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.streams = get_streams()

    @commands.is_owner()
    @commands.command()
    async def sync(self, ctx) -> None:
        logger.info("syncing...")
        # self.bot.tree.copy_global_to(guild=discord.Object(id=ID))
        syncom = await self.bot.tree.sync()  # guild=discord.Object(id=ID)
        logger.info(syncom)
        logger.info(f"synced {len(syncom)} commands: {', '.join([x.name for x in syncom])}")

    @staticmethod
    def shazam_file(guild_id):
        filename = f"file{guild_id}{datetime.now().strftime('%m%d%Y%H%M%S')}.mp3"
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    @staticmethod
    def add_streams(data: dict):
        with open(STREAMS, "w+") as file:
            file.write(json.dumps(data, sort_keys=True, indent=2))

    @staticmethod
    async def get_user_channel(i: Interaction):
        if i.user.voice is not None:
            return i.user.voice.channel
        await i.response.send_message("You're not in a voice channel")

    @app_commands.guild_only()
    @app_commands.command(name="radio", description="Play radio stream")
    @app_commands.describe(stream="Stream to play")
    @app_commands.choices(stream=[discord.app_commands.Choice(name=x, value=v) for x, v in get_streams().items()])
    async def radio(self, i: Interaction, stream: app_commands.Choice[str]):
        async def play_audio():
            await i.response.send_message(f"Started playing {stream.name}")
            source = await FFmpegOpusAudio.from_probe(stream.value, method='fallback')
            voice.play(source, after=lambda e: logger.error("It hath stopped: " + repr(e)))

            playing[i.guild.id] = stream.value
            logger.info(f"{i.guild.name} | {i.user.name} | {stream.name}")

        if (voice_channel := await self.get_user_channel(i)) is not None:
            voice = i.guild.voice_client
            if voice is None:
                voice = await voice_channel.connect()
                channels[i.guild.id] = voice_channel
            else:
                await self.stop(i)
                if voice.channel.name != voice_channel.name:
                    await voice.move_to(voice_channel)

            if voice.is_connected():
                await play_audio()

    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.command(name="shazam", description="Shazam current song")
    @app_commands.describe(duration="Optional parameter, defaults to 10s (can be between 10 and 20)")
    async def shazam(self, i: Interaction, duration: float = 10.0):
        async def record():
            source = playing[i.guild.id]
            response = urlopen(source, timeout=limit + 1.0)

            with open(filename, "wb") as file:
                while time() - start < limit:
                    try:
                        audio = response.read(1024)
                        if not audio:
                            return
                        file.write(audio)
                        await asyncio.sleep(0.01)
                    except Exception as e:
                        global recording_error
                        recording_error = True
                        logger.error(f"Record: {str(e)}")
                        return

        async def message_loading():
            count = 0
            while (check := time() - start) < limit:
                if check % limit >= count:
                    count += 1
                    await i.edit_original_response(content=f"Listening{' .' * count}")
                await asyncio.sleep(0.01)

        try:
            limit = float(duration)
            if limit < 10 or limit > 20:
                raise ValueError
        except ValueError:
            limit = 10.0

        if i.guild.voice_client is None or not i.guild.voice_client.is_playing():
            await i.response.send_message("Bot not playing")
            return

        if await self.get_user_channel(i) is None:
            return

        start = time()
        recording_error = False
        filename = self.shazam_file(i.guild.id)
        await i.response.send_message(content="Listening")

        loop = asyncio.get_event_loop()
        await asyncio.gather(*[loop.create_task(message_loading()), loop.create_task(record())])

        await i.edit_original_response(content="Shazaming")
        if recording_error:
            await i.edit_original_response(content="Recording error... ;_;")
            return

        shazam_output = await Shazam().recognize_song(filename)
        try:
            track = shazam_output["track"]["share"]["subject"]
            await i.edit_original_response(content=track)
        except KeyError:
            await i.edit_original_response(content="Nothing? Well... This is awkward... Try Again? heh")
        os.remove(filename)

    @app_commands.guild_only()
    @app_commands.command(name="disconnect", description="Disconnect bot from voice channel")
    async def disconnect(self, i: Interaction):
        voice_state = i.guild.voice_client
        if voice_state is None:
            await i.response.send_message("Not connected")
            return
        if voice_state.is_playing():
            del playing[i.guild.id]
            del channels[i.guild.id]

        await voice_state.disconnect(force=False)
        voice_state.cleanup()
        await i.response.send_message("Disconnected")

    async def stop(self, i: Interaction):
        try:
            del playing[i.guild.id]
        except KeyError:
            await i.response.send_message("Not playing anything")
            return
        voice = i.guild.voice_client
        if voice is not None:
            voice.stop()

    @commands.is_owner()
    @commands.command(name="add_stream")
    async def add_stream(self, ctx, *args):
        if len(args) != 2:
            return
        self.streams[args[0]] = args[1]
        self.add_streams(self.streams)
        await self.reload_streams(ctx)
        await ctx.send(f"Added {args[0]} to streams")

    @commands.is_owner()
    @commands.command(name="reload_streams")
    async def reload_streams(self, ctx, *args):
        self.streams = get_streams()

    @commands.is_owner()
    @commands.command(name="delete_stream")
    async def delete_stream(self, ctx, *args):
        if len(args) != 1:
            return
        if self.streams.get(args[0], None) is None:
            await ctx.send("No such entry")
            return
        del self.streams[args[0]]
        self.add_streams(self.streams)
        await ctx.send(f"Removed {args[0]} from streams")


async def setup(bot):
    await bot.add_cog(RadioCog(bot))
