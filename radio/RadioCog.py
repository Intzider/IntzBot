import asyncio
from datetime import datetime
from time import time
import json
import logging
import os
from urllib.request import urlopen

from discord import FFmpegOpusAudio, Embed
from discord.ext import commands
from shazamio import Shazam

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
    def shazam_file(guild_id):
        filename = f"file{guild_id}{datetime.now().strftime('%m%d%Y%H%M%S')}.mp3"
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    @staticmethod
    def add_streams(data: dict):
        with open(STREAMS, "w+") as file:
            file.write(json.dumps(data, sort_keys=True, indent=2))

    @staticmethod
    async def get_user_channel(ctx):
        if ctx.author.voice is not None:
            return ctx.author.voice.channel
        await ctx.send("You're not in a voice channel")

    async def verify_station(self, ctx, args):
        if len(args) != 1:
            embed = Embed()
            embed.add_field(name="Missing radio station name:",
                            value="\n".join([f"`{os.getenv('PREFIX')}play {x}`" for x, _ in self.bot.streams.items()]),
                            inline=False)
            await ctx.send(embed=embed)
            return

        if (station := self.bot.streams.get(args[0], None)) is None:
            await ctx.send("You mistyped, I ain't playin nuffin")
        else:
            if station == self.bot.playing.get(ctx.guild.id, None):
                await ctx.send("This is already playing")
                return
        return station

    @commands.guild_only()
    @commands.command(name="play")
    async def play(self, ctx, *args):
        async def play_audio():
            source = await FFmpegOpusAudio.from_probe(change, method='fallback')
            voice.play(source, after=lambda e: logger.error("It hath stopped: " + repr(e)))

            self.bot.playing[ctx.guild.id] = change
            logger.info(f"{ctx.guild.name} | {ctx.author.name} | {args[0]}")

        if (voice_channel := await self.get_user_channel(ctx)) is not None \
                and (change := await self.verify_station(ctx, args)) is not None:
            voice = ctx.guild.voice_client
            if voice is None:
                voice = await voice_channel.connect()
            else:
                await self.stop(ctx)
                if voice.channel != voice_channel:
                    voice.move_to(voice_channel)

            if voice.is_connected():
                await play_audio()

    @commands.guild_only()
    @commands.command("shazam")
    async def shazam(self, ctx, *args):
        async def record():
            source = self.bot.playing[ctx.guild.id]
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

        if await self.get_user_channel(ctx) is None:
            return

        start = time()
        recording_error = False
        filename = self.shazam_file(ctx.guild.id)
        message = await ctx.send("Listening")

        loop = asyncio.get_event_loop()
        await asyncio.gather(*[loop.create_task(message_loading()), loop.create_task(record())])

        await message.edit(content="Shazaming")
        if recording_error:
            await message.edit(content="Recording error... ;_;")
            return

        shazam_output = await Shazam().recognize_song(filename)
        try:
            track = shazam_output["track"]["share"]["subject"]
            await message.edit(content=track)
        except KeyError:
            await message.edit(content="Nothing? Well... This is awkward... Try Again? heh")
        os.remove(filename)

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
