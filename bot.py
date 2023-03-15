import os

from discord import FFmpegPCMAudio, Intents, utils, CategoryChannel
from discord.ext import commands

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TOKEN')
stream_url = "https://c2.hostingcentar.com/streams/radio101rock/"

bot = commands.Bot(intents=Intents().all(), command_prefix='!')


@bot.event
async def on_ready():
    print('Music Bot Ready')


@bot.command(name="play")
async def play(ctx):
    channel = ctx.author.voice
    if channel is None:
        await ctx.send("You're not in a voice channel")
        return

    if channel.channel is None:
        await ctx.send("You're not in a voice channel")
        return

    if 'voice' in globals():
        return

    global voice
    voice_channel = ctx.author.voice.channel
    voice = ctx.channel.guild.voice_client
    if voice is None:
        voice = await voice_channel.connect()
    elif voice.channel != voice_channel:
        voice.move_to(voice_channel)
    voice.play(FFmpegPCMAudio(stream_url))


@bot.command(name="stop")
async def stop(ctx):
    voice.stop()
    await disconnect(ctx)


@bot.command(name="dc")
async def disconnect(ctx):
    for x in bot.voice_clients:
        if x.channel == ctx.author.voice.channel:
            await x.disconnect(force=False)
            x.cleanup()
            del globals()['voice']


@bot.event
async def on_guild_available(guild):
    channel = utils.getchannel = utils.get(guild.text_channels, name='bot-channel')
    if channel is None:
        await guild.create_text_channel('bot-channel')


@bot.event
async def on_voice_state_update(member, before, after):
    voice_state = member.guild.voice_client
    if voice_state is None:
        return

    if len(voice_state.channel.members) == 1:
        await voice_state.disconnect()


bot.run(TOKEN)
