import asyncio
import json
import logging
import os
from time import time
from urllib.request import urlopen

from discord import FFmpegOpusAudio, Embed
from discord.ext import commands
from shazamio import Shazam

SHAZAM = os.path.join(os.path.dirname(os.path.abspath(__file__)), "file.mp3")
STREAMS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams.json")

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)


class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.streams = self.get_streams()
        self.bot.playing = dict()

    @staticmethod
    def get_streams() -> dict:
        with open(STREAMS, "r") as file:
            return json.load(file)

    @staticmethod
    def add_streams(data: dict):
        with open(STREAMS, "w+") as file:
            file.write(json.dumps(data, sort_keys=True, indent=2))

    @staticmethod
    async def get_user_channel(ctx):
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel")
            return None
        if ctx.author.voice.channel is None:
            await ctx.send("You're not in a voice channel")
            return None
        return ctx.author.voice.channel

    async def verify_station(self, ctx, args):
        if len(args) != 1:
            embed = Embed()
            embed.add_field(name="Missing radio station name:",
                            value="\n".join([f"`{os.getenv('PREFIX')}play {x}`" for x, _ in self.bot.streams.items()]),
                            inline=False)
            await ctx.send(embed=embed)
            return None

        if ctx.guild.voice_client is not None:
            if self.bot.streams.get(args[0], "") == ctx.guild.voice_client.endpoint:
                await ctx.send("This is already playing")
                return None

        station = self.bot.streams.get(args[0], None)
        if station is None:
            await ctx.send("You mistyped, I ain't playin nuffin")
            return None

        return station

    @commands.guild_only()
    @commands.command(name="play")
    async def play(self, ctx, *args):
        def play_audio(err=None):
            if err is not None:
                logger.error(f"play_audio {err}")
            if not voice.is_connected():
                return
            self.bot.playing[ctx.guild.id] = change
            source = FFmpegOpusAudio(change, options="-filter:a volume=0.2 -y")
            voice.play(source, after=lambda e: play_audio(e))

        voice_channel = await self.get_user_channel(ctx)
        voice = ctx.guild.voice_client
        change = await self.verify_station(ctx, args)

        if voice_channel is not None and change is not None:
            if voice is not None:
                if change is not None:
                    voice.pause()
                else:
                    return

            if voice is None:
                voice = await voice_channel.connect()
            elif voice.channel != voice_channel:
                voice.move_to(voice_channel)
            play_audio()

    @commands.guild_only()
    @commands.command("shazam")
    async def shazam(self, ctx, *args):
        async def record():
            source = self.bot.playing[ctx.guild.id]
            response = urlopen(source, timeout=limit + 1.0)

            with open(SHAZAM, "wb") as file:
                block_size = 1024
                while time() - start < limit:
                    try:
                        audio = response.read(block_size)
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
                    await message.edit(content=f"Listening{' .' * count}")
                await asyncio.sleep(0.01)

        if len(args) != 1:
            limit = 10.0
        else:
            try:
                limit = float(args[0])
                if limit < 10 or limit > 20:
                    raise ValueError
            except ValueError:
                await ctx.send("Can't even write a number between 10 and 20? Pathetic")
                limit = 10

        if ctx.guild.voice_client is None or not ctx.guild.voice_client.is_playing():
            await ctx.send("Bot not playing")
            return

        message = await ctx.send("Listening")
        start = time()

        recording_error = False
        loop = asyncio.get_event_loop()
        await asyncio.gather(*[loop.create_task(message_loading()), loop.create_task(record())])

        await message.edit(content="Shazaming")
        if recording_error:
            await message.edit(content="Recording error... ;_;")
            return

        shazam_output = await Shazam().recognize_song(SHAZAM)
        try:
            track = shazam_output["track"]["share"]["subject"]
            await message.edit(content=track)
        except KeyError:
            await message.edit(content="Nothing? Well... This is awkward... Try Again? heh")

    @commands.guild_only()
    @commands.command(name="dc")
    async def disconnect(self, ctx):
        voice_state = ctx.guild.voice_client
        if voice_state is None:
            return
        if voice_state.is_playing():
            del self.bot.playing[ctx.guild.id]

        await voice_state.disconnect()
        voice_state.cleanup()

    @commands.is_owner()
    @commands.command(name="pause")
    async def pause(self, ctx):
        voice = ctx.guild.voice_client
        if voice is not None:
            voice.pause() if voice.is_playing() else voice.resume()

    @commands.is_owner()
    @commands.command(name="resume")
    async def resume(self, ctx):
        await self.pause(ctx)

    @commands.is_owner()
    @commands.command(name="stop")
    async def stop(self, ctx):
        del self.bot.playing[ctx.guild.id]
        voice = ctx.guild.voice_client
        if voice is not None:
            voice.stop()
            await self.disconnect(ctx)

    @commands.is_owner()
    @commands.command(name="add_stream")
    async def add_stream(self, ctx, *args):
        if len(args) != 2:
            return
        self.bot.streams[args[0]] = args[1]
        self.add_streams(self.bot.streams)
        await self.reload_streams(ctx)
        await ctx.send(f"Added {args[0]} to streams")
        await self.play(ctx)

    @commands.is_owner()
    @commands.command(name="reload_streams")
    async def reload_streams(self, ctx, *args):
        self.bot.streams = self.get_streams()

    @commands.is_owner()
    @commands.command(name="delete_stream")
    async def delete_stream(self, ctx, *args):
        if len(args) != 1:
            return
        if self.bot.streams.get(args[0], None) is None:
            ctx.send("No such entry")
            return
        del self.bot.streams[args[0]]
        self.add_streams(self.bot.streams)
        await ctx.send(f"Removed {args[0]} from streams")
        await self.play(ctx)


async def setup(bot):
    await bot.add_cog(RadioCog(bot))
