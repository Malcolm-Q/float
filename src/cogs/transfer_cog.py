import discord
from discord import app_commands
from discord.ext import commands
import asyncio
from datetime import datetime
import os
import re
from src.utils import Config, convert_to_mb, format_time_difference, get_safe_guild_name, get_logger

CONFIG = Config.from_json()

class FileTransferCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.processes = {}
        self.logger = get_logger()

    @app_commands.command(name='upload', description='Upload a file to the bot')
    @app_commands.describe(code = "The code croc gave you")
    async def upload(self, interaction:discord.Interaction, code:str):
        if interaction.guild is None:
            raise ValueError("No guild found")
        self.logger.debug(f'INIT - /upload - {interaction.user.global_name} called /upload code:{code} in {interaction.guild.name}')
        guild = get_safe_guild_name(interaction.guild.name)
        self.init_guild_in_processes(guild)
        if len(self.processes[guild]) > CONFIG.max_active_processes:
            ctx = await commands.Context.from_interaction(interaction)
            await ctx.send("Too many active processes. Please try again later.", ephemeral=True)
            self.logger.info(f'USAGE - FAIL - /upload - {interaction.user.global_name} too many active processes in {interaction.guild.name} max_processes:{CONFIG.max_active_processes}, active_processes:{len(self.processes[guild])}')
            return
        args = [CONFIG.croc_path,"--overwrite", "--out", f"./files/{guild}/", code]
        self.logger.debug(f'RUN - /upload - {interaction.user.global_name} running: {args}')
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        pid = process.pid
        self.logger.debug(f'RUN - /upload - subprocess started with pid: {pid}')
        self.processes[guild][pid] = {
            'file': 'unknown',
            'time': datetime.now(),
            'owner': interaction.user.id,
            'process': process,
            'operation': 'upload',
            'cancelled': False,
            'active': True
        }
        file_size_mb = None
        file_name = ""
        msg = None
        if process.stdin is None or process.stderr is None:
            if process.returncode is None:
                process.terminate()
            self.logger.error(f'ERROR - /upload - {interaction.user.global_name} failed to start process with pid: {pid}')
            return
        try:
            file_name, file_size_mb = await self.get_name_and_size_from_croc(process)
            self.processes[guild][pid]['file'] = file_name
            ctx = await commands.Context.from_interaction(interaction)
            if file_size_mb is not None:
                if file_size_mb <= CONFIG.max_file_size_mb:
                    self.logger.info(f"USAGE - SUCCESS - /upload - {interaction.user.global_name} File {file_name} is {file_size_mb} MB")
                    process.stdin.write(b'y\n')
                    msg = await ctx.send("Uploading file...", ephemeral=True)
                else:
                    self.logger.info(f"USAGE - FAIL - /upload - {interaction.user.global_name} File {file_name} exceeds upload limit of {CONFIG.max_file_size_mb} MB")
                    self.logger.debug(f"EXITING - /upload - {pid} - CANCELLING UPLOAD")
                    process.stdin.write(b'n\n')
                    await ctx.send(f"File exceeds upload limit of {CONFIG.max_file_size_mb} MB", ephemeral=True)
                    self.processes[guild].pop(pid)
                    await process.wait()
                    self.logger.debug(f"EXITING - /upload - {pid} - PROCESS AWAITED")
                    if process.returncode is None:
                        self.logger.debug(f"EXITING - /upload - {pid} - PROCESS TERMINATED")
                        process.terminate()
                    else:
                        self.logger.debug(f"EXITING - /upload - {pid} - PROCESS EXITED GRACEFULLY")
                    return
            self.logger.debug(f"EXECUTING - /upload - {pid} - AWAITING UPLOAD PROCESS")
            await process.wait()
            self.logger.debug(f"EXECUTING - /upload - {pid} - PROCESS UPLOAD AWAITED")
        finally:
            if msg is not None and not self.processes[guild][pid]['cancelled']:
                await msg.edit(content="File uploaded!")
            if process.returncode is None:
                self.logger.debug(f"EXITING - /upload - {pid} - PROCESS TERMINATED")
                process.terminate()
            else:
                self.logger.debug(f"EXITING - /upload - {pid} - PROCESS EXITED GRACEFULLY")
            self.processes[guild].pop(pid)

    @app_commands.command(name='serve', description='Download a file from a bot')
    @app_commands.describe(file = "The name of the file")
    async def serve(self, interaction:discord.Interaction, file:str):
        if interaction.guild is None:
            raise ValueError("No guild found")
        self.logger.debug(f'INIT - /serve - {interaction.user.global_name} called /serve file:{file} in {interaction.guild.name}')
        guild = get_safe_guild_name(interaction.guild.name)
        self.init_guild_in_processes(guild)
        if len(self.processes[guild]) > CONFIG.max_active_processes:
            ctx = await commands.Context.from_interaction(interaction)
            await ctx.send("Too many active processes. Please try again later.", ephemeral=True)
            self.logger.info(f'USAGE - FAIL - /serve - {interaction.user.global_name} too many active processes in {interaction.guild.name} max_processes:{CONFIG.max_active_processes}, active_processes:{len(self.processes[guild])}')
        base_path = os.path.abspath(f'./files/{guild}')
        target_path = os.path.abspath(os.path.join(base_path, file))
        if not target_path.startswith(base_path):
            self.logger.warning(f'ABUSE - /serve - {interaction.user.global_name} attempted to access outside of guild folder\ntarget: {target_path}\narg: {file}')
            ctx = await commands.Context.from_interaction(interaction)
            await ctx.reply('Invalid file path!', ephemeral=True)
            return
        if not os.path.exists(f"./files/{guild}/{file}"):
            files = os.listdir(f'./files/{guild}')
            for f in files:
                if file.lower() in f.lower():
                    file = f
        file_size_mb = os.path.getsize(file) / (1024 * 1024)
        if file_size_mb > CONFIG.max_file_size_mb:
            ctx = await commands.Context.from_interaction(interaction)
            await ctx.reply(f"File exceeds download limit of {CONFIG.max_file_size_mb} MB", ephemeral=True)
            self.logger.info(f"USAGE - FAIL - /serve - {interaction.user.global_name} File {file} exceeds download limit of {CONFIG.max_file_size_mb} MB")
            return
        self.logger.debug(f"RUN - /serve - {interaction.user.global_name} starting croc for file: {file}")
        process = await asyncio.create_subprocess_exec(
            CONFIG.croc_path,"--yes", "send", f"./files/{guild}/"+file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        pid = process.pid
        self.logger.debug(f'RUN - /serve - subprocess started with pid: {pid}')
        self.processes[guild][pid] = {
            'file': file,
            'time': datetime.now(),
            'owner': interaction.user.id,
            'process': process,
            'operation': 'serve',
            'cancelled': False,
            'active': False
        }

        file_size = None
        code = None
        msg = None

        if process.stderr is None:
            if process.returncode is None:
                process.terminate()
            self.logger.error(f'ERROR - /serve - {interaction.user.global_name} failed to start process with pid: {pid}')
            return
        try:
            code, file_size = await self.get_code_from_croc(process)
            ctx = await commands.Context.from_interaction(interaction)
            if file_size and code:
                msg = await ctx.send(f"File size: {file_size}\nCode: {code}", ephemeral=True)
                self.logger.info(f"USAGE - SUCCESS - /serve - {interaction.user.global_name} File size: {file_size}, Code: {code}")
                while True:
                    try:
                        chunk = await asyncio.wait_for(process.stderr.read(1024), timeout=60)
                    except asyncio.TimeoutError:
                        process.kill()
                        self.processes[guild][pid]['cancelled'] = True
                        await msg.edit(content="Request cancelled!\nEnter the code within 60 seconds of requesting it.")
                        self.logger.info(f"USAGE - FAIL - /serve - {interaction.user.global_name} Request cancelled due to timeout")
                        break
                    if not chunk:
                        continue
                    if 'Sending' in chunk.decode():
                        self.processes[guild][pid]['active'] = True
                        break
            else:
                await ctx.send("Failed to extract file size or code.", ephemeral=True)
                self.logger.error(f"ERROR - /serve - {interaction.user.global_name} Failed to extract file size or code")
                process.kill()
            await process.wait()
        finally:
            if msg is not None and not self.processes[guild][pid]['cancelled']:
                await msg.edit(content="File served!")
            if process.returncode is None:
                self.logger.debug(f"EXITING - /serve - {pid} - PROCESS TERMINATED")
                process.terminate()
            else:
                self.logger.debug(f"EXITING - /serve - {pid} - PROCESS EXITED GRACEFULLY")
            await process.wait()
            if process in self.processes[guild]:
                self.processes[guild].pop(pid)

    @app_commands.command(name='ps', description='list active processes')
    async def ps(self, interaction:discord.Interaction):
        msg = ""
        if interaction.guild is None:
            raise ValueError("No guild found")
        self.logger.debug(f'INIT - /ps - {interaction.user.global_name} called /ps in {interaction.guild.name}')
        guild = get_safe_guild_name(interaction.guild.name)
        self.init_guild_in_processes(guild)
        for process, i in enumerate(self.processes[guild].keys()):
            formatted_time = format_time_difference(self.processes[guild][process]['time'], datetime.now())
            msg += f"\nProcess {i}:\n"
            msg += f"\tfile: {self.processes[guild][process]['file']}\n"
            msg += f"\towner: {self.processes[guild][process]['owner']}\n"
            msg += f"\ttime active: {formatted_time}\n"
            msg += f"\toperation: {self.processes[guild][process]['operation']}\n"
            msg += f"\tactive: {self.processes[guild][process]['active']}\n"
            msg += f"\tto kill use /kill {i}\n"
        if msg == "":
            msg = "No active processes"
        ctx = await commands.Context.from_interaction(interaction)
        await ctx.reply(msg, ephemeral=True)
        self.logger.info(f'USAGE - SUCCESS - /ps - {interaction.user.global_name} listed active processes in {interaction.guild.name}')

    @app_commands.command(name='kill', description='kill a process (use /ps to list)')
    @app_commands.describe(id = "the id of the process to kill")
    async def kill(self, interaction:discord.Interaction, id:int):
        if interaction.guild is None:
            raise ValueError("No guild found")
        self.logger.debug(f'INIT - /kill - {interaction.user.global_name} called /kill id:{id} in {interaction.guild.name}')
        guild = get_safe_guild_name(interaction.guild.name)
        ctx = await commands.Context.from_interaction(interaction)
        if len(self.processes[guild].keys()) < id:
            await ctx.reply("Invalid process id, use /ps", ephemeral=True)
            self.logger.info(f'USAGE - FAIL - /kill - {interaction.user.global_name} invalid process id:{id} in {interaction.guild.name}')
            return
        key = list(self.processes[guild].keys())[id]
        process = self.processes[guild][key]['process']
        self.logger.debug(f'RUN - /kill - {interaction.user.global_name} killing process id:{id} with pid:{process.pid}')
        process.kill()
        await process.wait()
        if process.returncode is None:
            process.terminate()
        self.processes[guild].pop(key)
        await ctx.reply(f"Process {id} killed.", ephemeral=True)
        self.logger.info(f'USAGE - SUCCESS - /kill - {interaction.user.global_name} killed process id:{id} in {interaction.guild.name}')

    def init_guild_in_processes(self, guild):
        if guild not in self.processes:
            self.processes[guild] = {}

    async def get_name_and_size_from_croc(self, process):
        buffer = ""
        file_name = ""
        file_size_mb = 0.0
        pid = process.pid

        self.logger.debug(f"RUN - /upload - reading process for pid: {pid}")
        i = 0
        while True:
            i += 1
            chunk = await process.stderr.read(1024)
            if not chunk:
                self.logger.debug(f"RUN - /upload - chunk {i} is falsey, breaking")
                break
            self.logger.debug(f"RUN - /upload - found chunk {i}")
            buffer += chunk.decode()
            
            match = re.search(r"Accept '(.+)' \(([\d.]+) (kB|MB|GB|B|TB)\)\? \(Y/n\)", buffer)
            if match:
                self.logger.debug(f"RUN - /upload - chunk {i} matched file size and name")
                file_name = match.group(1)
                size = float(match.group(2))
                unit = match.group(3)
                file_size_mb = convert_to_mb(size, unit)
                buffer = ""
                break
            
            match = re.search(r"Accept (\d+) files? and (\d+) folders? \(([\d.]+) (kB|MB|GB|B|TB)\)\? \(Y/n\)", buffer)
            if match:
                self.logger.debug(f"RUN - /upload - chunk {i} matched multiple files/folders")
                file_name = "folder"
                size = float(match.group(3))
                unit = match.group(4)
                file_size_mb = convert_to_mb(size, unit)
                buffer = ""
                break

        return file_name, file_size_mb

    async def get_code_from_croc(self, process):
        buffer = ""
        file_size = None
        code = None
        pid = process.pid

        self.logger.debug(f"RUN - /serve - reading process for pid: {pid}")
        i = 0
        while True:
            i += 1
            chunk = await process.stderr.read(1024)
            if not chunk:
                self.logger.debug(f"RUN - /serve - chunk {i} is falsey, breaking")
                break
            self.logger.debug(f"RUN - /serve - found chunk {i}")
            buffer += chunk.decode()
            size_match = re.search(r"Sending .* \((.*)\)", buffer)
            if size_match:
                self.logger.debug(f"RUN - /serve - chunk {i} matched file size")
                file_size = size_match.group(1)
            code_match = re.search(r"Code is: (.*)", buffer)
            if code_match:
                self.logger.debug(f"RUN - /serve - chunk {i} matched code")
                code = code_match.group(1)
            if file_size and code:
                self.logger.debug(f"RUN - /serve - chunk {i} matched both file size and code, breaking")
                break

        return code, file_size

async def setup(client):
  await client.add_cog(FileTransferCog(client))

