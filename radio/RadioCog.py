import asyncio
import json
import logging
import os
import shutil
from time import monotonic

import aiohttp
import discord
from discord import app_commands, Interaction
from discord.ext import commands
from shazamio import Shazam

DEFAULT_STREAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams.json")
# point STREAMS_FILE at a mounted volume so added/removed streams survive container rebuilds
STREAMS = os.getenv("STREAMS_FILE", DEFAULT_STREAMS)
MAX_CHOICES = 25  # Discord limit for autocomplete results

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)


def get_streams() -> dict:
    if not os.path.exists(STREAMS):
        os.makedirs(os.path.dirname(STREAMS), exist_ok=True)
        shutil.copyfile(DEFAULT_STREAMS, STREAMS)
    with open(STREAMS, "r") as file:
        return json.load(file)


class RadioCog(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        self.streams = get_streams()
        self.playing = dict()

    @commands.is_owner()
    @commands.command()
    async def sync(self, ctx) -> None:
        logger.info("syncing...")
        syncom = await self.bot.tree.sync()
        logger.info(f"synced {len(syncom)} commands: {', '.join([x.name for x in syncom])}")

    @staticmethod
    def add_streams(data: dict):
        with open(STREAMS, "w+") as file:
            file.write(json.dumps(data, sort_keys=True, indent=2))

    @staticmethod
    async def get_user_channel(i: Interaction):
        if i.user.voice is not None:
            return i.user.voice.channel
        await i.response.send_message("You're not in a voice channel", ephemeral=True)

    @staticmethod
    async def record(url: str, seconds: float) -> bytes:
        buffer = bytearray()
        timeout = aiohttp.ClientTimeout(total=seconds + 10.0, sock_connect=5.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                deadline = monotonic() + seconds
                async for chunk in response.content.iter_chunked(4096):
                    buffer.extend(chunk)
                    if monotonic() >= deadline:
                        break
        return bytes(buffer)

    @app_commands.guild_only()
    @app_commands.command(name="radio", description="Play radio stream")
    @app_commands.describe(stream="Stream to play")
    async def radio(self, i: Interaction, stream: str):
        url = self.streams.get(stream)
        if url is None:
            await i.response.send_message(f"Unknown station `{stream}`", ephemeral=True)
            return

        if (voice_channel := await self.get_user_channel(i)) is None:
            return

        # connecting can take longer than the 3s Discord allows for a response
        await i.response.defer()

        voice = i.guild.voice_client
        if voice is None:
            voice = await voice_channel.connect()
        else:
            voice.stop()
            if voice.channel != voice_channel:
                await voice.move_to(voice_channel)

        source = discord.FFmpegPCMAudio(
            url,
            before_options=(
                "-loglevel error "
                "-reconnect 1 "
                "-reconnect_streamed 1 "
                "-reconnect_delay_max 5"
            ),
            options="-vn",
        )
        voice.play(source, after=lambda e: logger.error(f"It hath stopped: {e!r}") if e else None)

        self.playing[i.guild.id] = url
        logger.info(f"{i.guild.name} | {i.user.name} | {stream}")
        await i.followup.send(f"Started playing {stream}")

    @radio.autocomplete("stream")
    async def radio_autocomplete(self, i: Interaction, current: str) -> list[app_commands.Choice[str]]:
        current = current.lower()
        return [
            app_commands.Choice(name=name, value=name)
            for name in sorted(self.streams) if current in name.lower()
        ][:MAX_CHOICES]

    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.command(name="shazam", description="Shazam current song")
    @app_commands.describe(duration="Seconds to listen, defaults to 10 (can be between 10 and 20)")
    async def shazam(self, i: Interaction, duration: app_commands.Range[float, 10, 20] = 10.0):
        async def message_loading():
            for count in range(1, int(duration) + 1):
                await i.edit_original_response(content=f"Listening{' .' * count}")
                await asyncio.sleep(1)

        url = self.playing.get(i.guild.id)
        if i.guild.voice_client is None or not i.guild.voice_client.is_playing() or url is None:
            await i.response.send_message("Bot not playing", ephemeral=True)
            return

        if await self.get_user_channel(i) is None:
            return

        await i.response.send_message(content="Listening")

        loading = asyncio.create_task(message_loading())
        try:
            audio = await self.record(url, duration)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Record: {e!r}")
            await i.edit_original_response(content="Recording error... ;_;")
            return
        finally:
            loading.cancel()

        await i.edit_original_response(content="Shazaming")
        try:
            shazam_output = await Shazam().recognize(audio)
            track = shazam_output["track"]["share"]["subject"]
        except KeyError:
            await i.edit_original_response(content="Nothing? Well... This is awkward... Try Again? heh")
            return
        except Exception as e:
            logger.error(f"Shazam: {e!r}")
            await i.edit_original_response(content="Shazam error... ;_;")
            return
        await i.edit_original_response(content=track)

    @app_commands.guild_only()
    @app_commands.command(name="disconnect", description="Disconnect bot from voice channel")
    async def disconnect(self, i: Interaction):
        logger.info(f'disconnected by: {i.user.name}')
        voice_state = i.guild.voice_client
        if voice_state is None:
            await i.response.send_message("Not connected", ephemeral=True)
            return
        self.playing.pop(i.guild.id, None)

        await voice_state.disconnect(force=False)
        await i.response.send_message("Disconnected")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # forget the stream when the bot leaves voice for any reason (kicked, auto-disconnect, ...)
        if member.id == self.bot.user.id and after.channel is None:
            self.playing.pop(member.guild.id, None)

    @commands.is_owner()
    @commands.command(name="add_stream")
    async def add_stream(self, ctx, *args):
        if len(args) != 2:
            return
        self.streams[args[0]] = args[1]
        self.add_streams(self.streams)
        await ctx.send(f"Added {args[0]} to streams")

    @commands.is_owner()
    @commands.command(name="reload_streams")
    async def reload_streams(self, ctx, *args):
        self.streams = get_streams()
        await ctx.send(f"Reloaded {len(self.streams)} streams")

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
