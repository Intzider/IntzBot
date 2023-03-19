import json
import os

from discord import FFmpegOpusAudio
from discord.ext import commands


def get_streams() -> dict:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams.json"), "r") as file:
        return json.load(file)


def add_streams(data: dict):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "streams.json"), "w+") as file:
        file.write(json.dumps(data, indent=4))


class RadioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.streams = get_streams()

    async def get_user_channel(self, ctx):
        if ctx.author.voice is None:
            await ctx.send("You're not in a voice channel")
            return None
        if ctx.author.voice.channel is None:
            await ctx.send("You're not in a voice channel")
            return None
        return ctx.author.voice.channel

    async def verify_station(self, ctx, args):
        if len(args) != 1:
            message = "Missing radio station argument:\n"
            message += "\n".join(
                [f"    {os.getenv('PREFIX')}play {x}" for x, v in self.bot.streams.items()])
            await ctx.send(message)
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

    @commands.command(name="play")
    async def play(self, ctx, *args):
        def play_audio(err=None):
            if err is not None:
                print(err)
            if not voice.is_connected():
                return
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

    @commands.command(name="pause")
    async def pause(self, ctx):
        voice = ctx.guild.voice_client
        if voice is not None:
            voice.pause() if voice.is_playing() else voice.resume()

    @commands.command(name="resume")
    async def resume(self, ctx):
        await self.pause(ctx)

    @commands.command(name="stop")
    async def stop(self, ctx):
        voice = ctx.guild.voice_client
        if voice is not None:
            voice.stop()
            await self.disconnect(ctx)

    @commands.command(name="dc")
    async def disconnect(self, ctx):
        voice_state = ctx.guild.voice_client
        if voice_state is None:
            return

        await voice_state.disconnect()
        voice_state.cleanup()

    @commands.is_owner()
    @commands.command(name="add_stream")
    async def add_stream(self, ctx, *args):
        if len(args) != 2:
            return
        self.bot.streams[args[0]] = args[1]
        add_streams(self.bot.streams)
        await ctx.send(f"Added {args[0]} to streams")
        await self.play(ctx)

    @commands.is_owner()
    @commands.command(name="delete_stream")
    async def add_stream(self, ctx, *args):
        if len(args) != 1:
            return
        if self.bot.streams.get(args[0], None) is None:
            ctx.send("No such entry")
            return
        del self.bot.streams[args[0]]
        add_streams(self.bot.streams)
        await ctx.send(f"Removed {args[0]} from streams")
        await self.play(ctx)


async def setup(bot):
    await bot.add_cog(RadioCog(bot))
