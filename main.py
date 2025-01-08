import discord
from discord.ext import commands
from dotenv import load_dotenv 
import os
from src.utils import get_logger

load_dotenv()

intents = discord.Intents.all()
client = commands.Bot(command_prefix='/',intents=intents)
bot_token = os.environ['BOT_TOKEN']

@client.event
async def on_ready():
    logger = get_logger()
    try:
        await client.load_extension('src.cogs.transfer_cog')
        await client.load_extension('src.cogs.file_management_cog')
        synced = await client.tree.sync()
        logger.debug(f'synced {len(synced)} commands')
    except Exception as e:
        logger.error(f'failed to load cogs and sync tree: {e}')
    logger.info(f'Logged in as {client.user}')

client.run(bot_token)
