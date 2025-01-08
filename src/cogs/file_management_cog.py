from datetime import datetime
import discord
from discord import app_commands
from discord.ext import commands
from src.utils import get_safe_guild_name, get_logger
import os

class FileManagementCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.logger = get_logger()

    @app_commands.command(name='mv', description='move a file (don\'t forget the file extension!)')
    @app_commands.describe(target = 'the name of the file to move')
    @app_commands.describe(output = 'the new name of the file')
    async def mv(self, interaction:discord.Interaction, target:str, output:str):
        if interaction.guild is None:
            return
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.reply('working...')
        self.logger.debug(f'INIT - /mv - {interaction.user.global_name} called /mv target:{target} output:{output} in {interaction.guild.name}')
        ctx = await commands.Context.from_interaction(interaction)
        server = get_safe_guild_name(interaction.guild.name)
        base_path = os.path.abspath(f'./files/{server}')
        target_path = os.path.abspath(os.path.join(base_path, target))
        output_path = os.path.abspath(os.path.join(base_path, output))
        if not target_path.startswith(base_path) or not output_path.startswith(base_path):
            self.logger.warning(f'ABUSE - /mv - {interaction.user.global_name} attempted to delete outside of server folder\ntarget: {target_path}\narg: {target}\noutput: {output_path}\narg: {output}')
            await ctx.reply('Invalid file path!', ephemeral=True)
            return
        if not os.path.exists(target_path):
            self.logger.info(f'USAGE - FAIL - /mv - {interaction.user.global_name} attempted to move non-existent file: {target_path} to: {output_path}')
            await ctx.reply(f'Could not find {target} to move!\nCall /ls', ephemeral=True)
            return
        if os.path.exists(output_path):
            self.logger.info(f'USAGE - FAIL - /mv - {interaction.user.global_name} attempted to move file: {target_path} to existing path: {output_path}')
            await ctx.reply(f'{output} already exists!\nCall /rm to delete it or rename it first', ephemeral=True)
            return
        os.rename(target_path, output_path)
        self.logger.info(f'USAGE - SUCCESS - /mv - {interaction.user.global_name} moved: {target_path} to: {output_path}')
        await ctx.reply(f'Moved {target} to {output}', ephemeral=True)

    @app_commands.command(name='ls', description='list downloadable files')
    @app_commands.describe(filter='A sub string to filter results by')
    @app_commands.describe(folder='The folder to list the contents of')
    async def ls(self, interaction: discord.Interaction, filter: str = '', folder: str = './'):
        '''
        List files 
        '''
        if interaction.guild is None:
            return
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.reply('working...')
        self.logger.debug(f'INIT - /ls - {interaction.user.global_name}, filter:{filter}, folder:{folder}, in {interaction.guild.name}')
        ctx = await commands.Context.from_interaction(interaction)
        server = get_safe_guild_name(interaction.guild.name)
        base_path = os.path.abspath(f'./files/{server}')
        target_path = os.path.abspath(os.path.join(base_path, folder))

        if not target_path.startswith(base_path):
            self.logger.warning(f'ABUSE - /ls - {interaction.user.global_name} attempted to list outside of server folder\ntarget: {target_path}\narg: {folder}')
            await ctx.reply('Invalid folder path!', ephemeral=True)
            return

        if not os.path.exists(target_path) or not os.path.isdir(target_path):
            self.logger.info(f'USAGE - FAIL - /ls - {interaction.user.global_name} attempted to list non-existent folder: {target_path}')
            await ctx.reply(f'Could not find folder {folder}!\nCall /ls', ephemeral=True)
            return

        files = os.listdir(target_path)
        
        if filter:
            files = [f for f in files if filter.lower() in f.lower()]

        if len(files) == 0:
            self.logger.info(f'USAGE - SUCCESS - /ls - {interaction.user.global_name} listed empty folder: {target_path} in {interaction.guild.name}')
            await ctx.reply('No files found', ephemeral=True)
            return

        file_details = []
        for file in files:
            file_path = os.path.join(target_path, file)
            if os.path.isfile(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)
                modified_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                file_details.append(f'{file} - Size: {size:.2f} MB - Modified: {modified_time}')
            else:
                file_details.append(f'{file} - [Directory]')

        self.logger.info(f'USAGE - SUCCESS - /ls - {interaction.user.global_name} listed folder: {target_path} in {interaction.guild.name}')
        await ctx.send('\n'.join(file_details), ephemeral=True)

    @app_commands.command(name='rm', description='Delete a file')
    @app_commands.describe(file = 'The file or folder to delete')
    async def rm(self, interaction:discord.Interaction, file:str):
        if interaction.guild is None:
            return
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.reply('working...')
        self.logger.debug(f'INIT - /rm - {interaction.user.global_name}, file:{file} in {interaction.guild.name}')
        ctx = await commands.Context.from_interaction(interaction)
        server = get_safe_guild_name(interaction.guild.name)
        base_path = os.path.abspath(f'./files/{server}')
        target_path = os.path.abspath(os.path.join(base_path, file))
        self.logger.debug(f'RESULT - base_path: {base_path} target_path: {target_path}')
        if not target_path.startswith(base_path):
            self.logger.warning(f'ABUSE - /rm - {interaction.user.global_name} attempted to delete outside of server folder\ntarget: {target_path}\narg: {file}')
            await ctx.reply('Invalid file path!', ephemeral=True)
            return
        if target_path == base_path:
            self.logger.warning(f'ABUSE - /rm - {interaction.user.global_name} attempted to delete server folder\ntarget: {target_path}\narg: {file}')
            await ctx.reply('Invalid file path!', ephemeral=True)
            return
        if not os.path.exists(target_path):
            self.logger.info(f'USAGE - FAIL - /rm - {interaction.user.global_name} attempted to delete non-existent file: {target_path}')
            await ctx.reply(f'Could not find {file} to delete!\nCall /ls', ephemeral=True)
            return
        os.remove(target_path)
        self.logger.info(f'USAGE - SUCCESS - /rm - {interaction.user.global_name} deleted: {target_path}')
        await ctx.reply(f'Deleted {file}', ephemeral=True)

async def setup(client):
  await client.add_cog(FileManagementCog(client))

