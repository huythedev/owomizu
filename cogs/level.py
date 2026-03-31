"""
Mizu OwO Bot
Copyright (C) 2025 MizuNetwork
Copyright (C) 2025 Kiy0w0
"""

import string
import random
import os


from discord.ext import commands
from discord.ext.commands import ExtensionNotLoaded
import asyncio



quotes_url = "https://favqs.com/api/qotd"
SENTENCES_FILE = "config/sentences.txt"

def generate_random_string(min, max):
    """something like a list?"""
    characters = string.ascii_lowercase + ' '
    length = random.randint(min,max)
    random_string = "".join(random.choice(characters) for _ in range(length))
    return random_string

async def fetch_quotes(session):
    async with session.get(quotes_url) as response:
        if response.status == 200:
            data = await response.json()
            quote = data["quote"]["body"]  # data[0]["quote"]
            return quote


def load_sentences_from_file(path=SENTENCES_FILE):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            # Each non-empty line is treated as a sentence candidate.
            return [line.strip() for line in f if line.strip()]
    except OSError:
        return []



class Level(commands.Cog):
    def __init__(self, bot):
        
        self.bot = bot
        self.last_level_grind_message = None
        self.cmd = {
            "cmd_name": None,
            "prefix": False,
            "checks": True,
            "id": "level"
        }
        self.sentences = []

    def _pick_level_message(self, cnf):
        if cnf.get("useQuoteInstead", False):
            if self.sentences:
                return random.choice(self.sentences)
            return None
        return generate_random_string(cnf["minLengthForRandomString"], cnf["maxLengthForRandomString"])

    async def start_level_grind(self):
        #await asyncio.sleep(1)
        await self.bot.remove_queue(id="level")
        cnf = self.bot.settings_dict["commands"]["lvlGrind"]
        try:
            self.sentences = load_sentences_from_file()
            await self.bot.sleep_till(cnf["cooldown"])
            self.last_level_grind_message = self._pick_level_message(cnf)
            if self.last_level_grind_message is None:
                # Fallback to API quote when sentence file has no usable lines.
                self.last_level_grind_message = await fetch_quotes(self.bot.session)
            if not self.last_level_grind_message:
                self.last_level_grind_message = generate_random_string(cnf["minLengthForRandomString"], cnf["maxLengthForRandomString"])
            self.cmd["cmd_name"] = self.last_level_grind_message

            await self.bot.put_queue(self.cmd)
        except Exception as e:
            await self.bot.log(f"Error - start_level_grind(): {e}", "#c25560")
        
    
    """gets executed when the cog is first loaded"""
    async def cog_load(self):
        if not self.bot.settings_dict["commands"]["lvlGrind"]["enabled"]:
            try:
                asyncio.create_task(self.bot.unload_cog("cogs.level"))
            except ExtensionNotLoaded:
                pass
        else:
            asyncio.create_task(self.start_level_grind())

    async def cog_unload(self):
        await self.bot.remove_queue(id="level")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == self.bot.cm.id and message.author.id == self.bot.user.id:
            if self.last_level_grind_message == message.content:
                await self.start_level_grind()
                

async def setup(bot):
    await bot.add_cog(Level(bot))