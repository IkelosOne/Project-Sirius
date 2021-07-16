# Imports
from random import randint
from datetime import date, datetime
import json
import socket
import discord
import re  # Remove this later lol


# Home imports
from log_handling import *
from imaging import generate_rank_card
from upgrade_json import server_structure
import on_message


# Variables
PREFIX = "-"
with open("token.txt") as file:
	DISCORD_TOKEN = file.read()


# Definitions
class MyClient(discord.Client):

	def __init__(self, debug=False, *args, **kwargs):

		super().__init__(*args, **kwargs)
		self.start_time = datetime.now()
		self.data = {}
		self.cache = {}
		self.activity = discord.Activity(type=discord.ActivityType.listening, name="the rain")

		# Print logs to the console too (for debugging)
		if debug is True:
			logger.addHandler(logging.StreamHandler())

	def update_data(self):
		"""Writes the data attribute to the file."""

		try:
			with open("data.json", "w", encoding='utf-8') as file:
				json.dump(self.data, file, indent=4)
			logger.debug("Updated data.json")  # Event log
		except:
			logger.critical("Failed to update data.json")  # Event log

	def initialise_guild(self, guild):
		"""Creates data for a new guild."""

		try:
			self.data["servers"][str(guild.id)] = server_structure
			self.cache[str(guild.id)] = {}

			# Write the updated data
			self.update_data()
			logger.info("Initialised guild: " + guild.name + " (ID: " + str(guild.id) + ")")  # Event log
		except:
			logger.critical("Failed to initialise guild: " + guild.name + " (ID: " + str(guild.id) + ")")  # Event log

	def get_uptime(self):
		"""Returns client uptime as a string."""

		try:
			seconds = (datetime.now() - self.start_time).seconds
			uptime = ""
			if seconds >= 3600:
				uptime += str(seconds // 3600) + " "
				if seconds // 3600 == 1:
					uptime += "hour"
				else:
					uptime += "hours"
			if seconds % 3600 >= 60:
				if uptime != "":
					uptime += " "
				uptime += str(seconds % 3600 // 60) + " "
				if seconds % 3600 // 60 == 1:
					uptime += "minute"
				else:
					uptime += "minutes"
			if seconds % 60 > 0:
				if uptime != "":
					uptime += " "
				uptime += str(seconds % 60) + " "
				if seconds % 60 == 1:
					uptime += "second"
				else:
					uptime += "seconds"

			logger.debug("Calculated uptime")  # Event log
			return uptime
		except:
			logger.error("Failed to calculate uptime")  # Event log
			return None

	async def on_ready(self):
		"""Runs when the client is ready."""

		logger.info(self.user.name + " is ready (commencing on_ready)")  # Event log
		if self.guilds != []:
			logger.info(self.user.name + " is connected to the following guilds:")  # Event log
			for guild in self.guilds:
				logger.info("    " + guild.name + " (ID: " + str(guild.id) + ")")  # Event log

		# Load the data file into the data variable
		try:
			with open("data.json", encoding='utf-8') as file:
				self.data = json.load(file)
			logger.debug("Loaded data.json")  # Event log
		except:
			logger.critical("Could not load data.json")  # Event log

		# Check if Sirius has been added to a guild while offline
		for guild in self.guilds:
			if str(guild.id) not in self.data["servers"]:
				logger.warning("Sirius is in " + guild.name + " but has no data for it")  # Event log

				# Initialise guild
				self.initialise_guild(guild)

		# Initialise cache for servers
		for guild in self.guilds:
			self.cache[str(guild.id)] = {}

		logger.info(self.user.name + " is ready (finished on_ready)")  # Event log

	async def on_guild_join(self, guild):
		"""Runs on joining a guild."""

		logger.info(self.user.name + " has joined the guild: " + guild.name + " with id: " + str(guild.id))  # Event log

		# Check if server data already exists
		if str(guild.id) not in self.data["servers"]:

			# Initialise guild
			self.initialise_guild(guild)

	async def on_message(self, message):
		"""Runs on message."""

		logger.debug("Message sent by " + message.author.name)  # Event log

		# Don't respond to yourself
		if message.author.id == self.user.id:
			return

		# Don't respond to other bots
		if message.author.bot is True:  # !!! Needs to be tested
			return

		# Set guild of origin
		guild = self.get_guild(message.guild.id)

		# Update the user's experience
		if (message.author.id not in self.cache[str(guild.id)]) or ((datetime.now() - self.cache[str(guild.id)][
			message.author.id]).seconds // 3600 > 0):  # This is the longest like of code I've ever seen survive a scrutinised and picky merge from me. Well played.

			logger.debug("Adding experience to " + message.author.name)  # Event log

			# Update the cache and increment the user's experience
			self.cache[str(guild.id)][message.author.id] = datetime.now()
			try:
				self.data["servers"][str(guild.id)]["ranks"][str(message.author.id)] += 1
			except KeyError:
				self.data["servers"][str(guild.id)]["ranks"][str(message.author.id)] = 1


			# Write the updated data
			self.update_data()
		else:
			logger.debug("Not adding experience to " + message.author.name)  # Event log

		# Get rank command
		if message.content.startswith(PREFIX + "get rank"):

			logger.info("`get rank` called by " + message.author.name)  # Event log

			# Generate the rank card
			if str(message.author.id) in self.data["servers"][str(guild.id)]["ranks"]:
				rank = int((self.data["servers"][str(guild.id)]["ranks"][str(message.author.id)] ** 0.5) // 1)
				percentage = int(round((self.data["servers"][str(guild.id)]["ranks"][str(message.author.id)] - (
						rank ** 2)) / (((rank + 1) ** 2) - (rank ** 2)) * 100))
			else:
				rank = 0
				percentage = 0
			generate_rank_card(message.author.avatar_url, message.author.name, rank, percentage)

			# Create the rank embed
			embed_rank = discord.Embed()
			file = discord.File("card.png")
			embed_rank.set_image(url="attachment://card.png")

			# Send the embed
			await message.channel.send(file=file)

		# Embed command
		if message.content.startswith(PREFIX + "embed"):
			embed = discord.Embed(title="👋 Welcome to " + message.guild.name + ".", description="[Discord community server description]\n\nTake a moment to familiarise yourself with the rules below.\nChannel <#831953098800889896> is for this, and <#610595467444879421> is for that.", color=0xffc000)

			argument_string = message.content[len(PREFIX + "embed "):]
			arguments = re.split(",(?!\s)", argument_string)  # Splits arguments when there is not a space after the comma, if there is, it is assumed to be part of a sentance.
			title = message.author.name
			description = "Says:"
			fields = []

			# Analyse argument
			for argument in arguments:
				argument = argument.split("=")
				print("Argument 0, 1:", argument[0], argument[1])
				if argument[0] == "title":
					title = argument[1]
				elif argument[0] == "description":
					description = argument[1]
				else:
					fields.append({argument[0]:argument[1]})

			# Create and send poll embed
			embed = discord.Embed(title=title, description=description, color=0xffc000)
			for field in fields:
				embed.add_field(name=list(field.keys())[0],value=field[list(field.keys())[0]])

			await message.channel.send(embed=embed)

		# If the message was sent by the admins
		if guild.get_role(self.data["servers"][str(message.guild.id)]["config"][
			                  "admin role id"]) in guild.get_member(message.author.id).roles:

			# Rules command
			if message.content == PREFIX + "rules":

				logger.info("`rules` called by " + message.author.name)  # Event log

				# Delete the command message
				await message.channel.purge(limit=1)

				# Create the welcome embed !!! This is messy. Decide embed format and what should be customisable
				embed_welcome = discord.Embed(title="👋 Welcome to " + message.guild.name + ".", description="[Discord community server description]\n\nTake a moment to familiarise yourself with the rules below.\nChannel <#831953098800889896> is for this, and <#610595467444879421> is for that.", color=0xffc000)

				# Create the rules embed
				embed_rules = discord.Embed(title=self.data["servers"][str(guild.id)]["rules"]["title"], description=
				self.data["servers"][str(guild.id)]["rules"]["description"], color=0xffc000, inline=False)
				embed_rules.set_footer(text="Rules updated: • " + date.today().strftime("%d/%m/%Y"), icon_url=guild.icon_url)
				embed_rules.add_field(name="Rules", value="\n".join(
					self.data["servers"][str(guild.id)]["rules"]["list"]), inline=True)

				embed_image = discord.Embed(description="That's all.", color=0xffc000)
				image = self.data["servers"][str(guild.id)]["rules"]["image link"]
				try:
					embed_image.set_image(url=self.data["servers"][str(guild.id)]["rules"]["image link"])
				except:
					logger.debug("Image link non-existant for " + str(message.guild.id))  # Event log

				# Send the embeds
				await message.channel.send(embed=embed_welcome)
				await message.channel.send(embed=embed_rules)
				await message.channel.send(embed=embed_image)

			# Roles command
			if message.content == PREFIX + "roles":

				logger.info("`roles` called by " + message.author.name)  # Event log

				# Delete the command message
				await message.channel.purge(limit=1)

				# Send one roles message per category
				await message.channel.send("🗒️ **Role selection**\nReact to get a role, unreact to remove it.")
				for category in self.data["servers"][str(guild.id)]["roles"]["category list"]:  # For category in roles list
					roles = []
					for role in self.data["servers"][str(guild.id)]["roles"]["category list"][category][
						"role list"]:  # For role in category
						roles.append(
							self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"][role][
								"emoji"] + " - " +
							self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"][role][
								"name"] + "\n")
					category_message = await message.channel.send("**" + category + "**\n\n" + "".join(roles))

					# Add reactions to the roles message
					for role in self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"]:
						await category_message.add_reaction(
							self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"][role][
								"emoji"])

					# Update the category's message id variable
					self.data["servers"][str(guild.id)]["roles"]["category list"][category][
						"message id"] = category_message.id

				# Write the updated data
				self.update_data()

			# Stats command
			if message.content == PREFIX + "stats":
				"""THINGS TO FIX:

				- Trailing newlines at the end of embed"""

				logger.info("`stats` called by " + message.author.name)  # Event log

				# Generate statistics
				waiting_message = await message.channel.send("This may take some time...")
				try:
					members = {}
					channel_statistics = ""
					member_statistics = ""
					for channel in guild.text_channels:
						message_count = 0
						async for message_sent in channel.history(limit=None):
							message_count += 1
							# Don't count bot messages
							if message_sent.author.bot is False:
								if message_sent.author not in members:
									members[message_sent.author] = 1
								else:
									members[message_sent.author] += 1
						channel_statistics += channel.name + ": " + str(message_count) + "\n"
					for member in members:
						member_statistics += member.name + ": " + str(members[member]) + "\n"
					logger.debug("Successfully generated statistics")
				except UnicodeEncodeError:
					logger.error("Username " + message_sent.author.name + " was too advanced to handle")
					await message.channel.send("Stats Failed: A username cannot be read")
				except Exception as exception:
					logger.error("Failed to generate statistics. Exception: " + str(exception))
					await message.channel.send("Stats Failed: Unknown error")

				# Create and send statistics embed
				embed_stats = discord.Embed(title="📈 Statistics for " + guild.name, color=0xba5245)
				embed_stats.add_field(name="Channels", value=channel_statistics)
				embed_stats.add_field(name="Members", value=member_statistics)
				embed_stats.set_footer(text="Statistics updated • " + date.today().strftime("%d/%m/%Y"), icon_url=guild.icon_url)
				await waiting_message.delete()
				await message.channel.send(embed=embed_stats)

			# Poll command
			if message.content.startswith(PREFIX + "poll"):
				"""ERRORS TO TEST FOR:

				- Duplicate emojis
				- Custom emojis
				- Duplicate custom emojis

				THINGS TO FIX:

				- Standardise datetime format
				- Remove regex secretly
				- Trailing newlines at the end of embed
				"""

				logger.info("`poll` called by " + message.author.name)  # Event log

				# Delete the command message
				await message.channel.purge(limit=1)

				# !!! Clunky and breakable
				argument_string = message.content[len(PREFIX + "poll "):]
				arguments = re.split("\,\s|\,", argument_string)  # Replace with arguments = argument.split(", ")
				candidates = {}  # Dictionary of candidates that can be voted for
				candidates_string = ""

				# Analyse argument
				for argument in arguments:
					argument = argument.split("=")
					print("Argument 0, 1:", argument[0], argument[1])
					poll_time = str(datetime.now())
					if argument[0] == "title":
						title = argument[1]
					elif argument[0] == "time":

						# Arun's time machine
						time_list = argument[1].split("/")
						hour = 12
						minute = 00
						if ":" in time_list[2]:
							last_time_arg = time_list[2].split(" ")
							time_list[2] = last_time_arg[0]
							hour = last_time_arg[1].split(":")[0]
							minute = last_time_arg[1].split(":")[1]
						poll_time = str(datetime(day=int(time_list[0]), month=int(time_list[1]), year=int(time_list[
							                                                                                  2]), hour=int(hour), minute=int(minute)))  # Accommodate for American convention. Or don't.

					else:
						candidates[argument[1].rstrip()] = argument[0]
						candidates_string += argument[1] + " - " + argument[0] + "\n"

				# Create and send poll embed
				embed_poll = discord.Embed(title=title, description=candidates_string, color=0xffc000)
				embed_poll.set_footer(text="Poll ending • " + poll_time)
				poll_message = await message.channel.send(embed=embed_poll)

				# Add reactions to the poll embed
				for candidate in candidates:
					print("Candidate: " + str(candidate))
					await poll_message.add_reaction(candidate)

		# If the message was sent by the developers
		if message.author.id in self.data["config"]["developers"]:

			# Locate command
			if message.content == PREFIX + "locate":
				logger.info("`locate` called by " + message.author.name)  # Event log
				hostname = socket.gethostname()
				await message.channel.send("This instance is being run on **" + hostname + "**, IP address **" + socket.gethostbyname(hostname) + "** (**" + str(round(self.latency*10000)/10000) + "**ms)" + "\nUptime: " + self.get_uptime() + ".")

			# Kill command
			if message.content.startswith(PREFIX + "kill"):

				logger.info("`kill` called by " + message.author.name)  # Event log

				# !!! Clunky and breakable?
				argument = message.content[len(PREFIX + "kill "):]
				if self.data["config"]["jokes"] is True:
					await message.channel.send("Doggie down")
				await message.channel.send(self.user.name + " shutting down.\nUptime: " + self.get_uptime() + ".\n" + argument)
				await client.close()

		# Joke functionality
		if self.data["config"]["jokes"] is True:

			# Joke functionality: Shut up Arun
			if message.author.id == 258284765776576512:

				# logger.info("Arun sighted. Locking on")  # Event log

				if randint(1, 25) == 1:
					if randint(1, 2) == 1:
						await message.channel.send("shut up arun")
					else:
						await message.channel.send("arun, why are you still talking")
				# logger.info("Arun down.")  # Event log
				else:
					pass
			# logger.info("Mission failed, RTB")  # Event log

			# Joke functionality: Shut up Pablo
			if message.author.id == 241772848564142080 or message.author.id == 842479806217060363:

				logger.info("Pablo sighted. Locking on")  # Event log

				if randint(1, 25) == 1:
					logger.info("Revenge protocol ready: affirmative")
					if randint(1, 2) == 1:
						await message.channel.send("shut up pablo")
					else:
						await message.channel.send("pablo, put that big brain back on sleep mode")
					logger.info("Pablo down.")  # Event log
				else:
					logger.info("Mission failed, RTB")  # Event log

			# Gameboy mention
			if "gameboy" in message.content.lower():
				logger.debug("`gameboy` mentioned by " + message.author.name)  # Event log
				await message.channel.send("Gameboys are worthless (apart from micro. micro is cool)")

			# Raspberry mention
			if "raspberries" in message.content.lower() or "raspberry" in message.content.lower():
				logger.debug("`raspberry racers` mentioned by " + message.author.name)  # Event log
				await message.channel.send("The Raspberry Racers are a team which debuted in the 2018 Winter Marble League. Their 2018 season was seen as the second-best rookie team of the year, behind only the Hazers. In the 2018 off-season, they won the A-Maze-ing Marble Race, making them one of the potential title contenders for the Marble League. They eventually did go on to win Marble League 2019.")

			# Pycharm mention
			if "pycharm" in message.content.lower():
				logger.debug("`pycharm` mentioned by " + message.author.name)  # Event log
				await message.channel.send("Pycharm enthusiasts vs Sublime Text enjoyers: https://youtu.be/HrkNwjruz5k")
				await message.channel.send("85 commits in and haha bot print funny is still your sense of humour.")

			# Token command
			if message.content == PREFIX + "token":
				logger.debug("`token` called by " + message.author.name)  # Event log
				await message.channel.send("IdrOppED ThE TokEN gUYS!!!!")

			# Summon lizzie command
			if message.content == PREFIX + "summon_lizzie":
				logger.debug("`summon_lizzie` called by " + message.author.name)  # Event log
				for x in range(100):
					await message.channel.send(guild.get_member(692684372247314445).mention)

			# Summon leo command
			if message.content == PREFIX + "summon_leo":
				logger.debug("`summon_leo` called by " + message.author.name)  # Event log
				for x in range(100):
					await message.channel.send(guild.get_member(242790351524462603).mention)

			# Teaching bitches how to swim
			if message.content == PREFIX + "swim":
				logger.debug("`swim` called by " + message.author.name)  # Event log
				await message.channel.send("/play https://youtu.be/uoZgZT4DGSY")
				await message.channel.send("No swimming lessons today ):")

			# Overlay Israel (Warning: DEFCON 1)
			if message.content == PREFIX + "israeli_defcon_1":
				logger.debug("`israeli_defcon_1` called by " + message.author.name)  # Event log
				await message.channel.send("preemptive apologies...")
				while True:
					await message.channel.send(".overlay israel")

	async def on_member_join(self, member):
		"""Runs when a member joins."""

		logger.debug("Member " + member.name + " joined guild " + member.guild.name)
		try:
			await member.create_dm()
			await member.dm_channel.send("Welcome to "+member.guild.name+", " + member.name + ".")
			logger.debug("Sent welcome message to " + member.name)  # Event log
		except:
			# If user has impeded direct messages
			logger.debug("Failed to send welcome message to " + member.name)  # Event log

	async def on_member_remove(self, member):
		"""Runs when a member leaves."""

		logger.debug("Member " + member.name + " left guild [GUILD_NAME]")
		try:
			await member.create_dm()
			await member.dm_channel.send("Goodbye ;)")
			logger.debug("Sent goodbye message to " + member.name)  # Event log
		except:
			# If the user has impeded direct messages
			logger.debug("Failed to send goodbye message to " + member.name)  # Event log

	async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
		"""Gives a role based on a reaction emoji."""

		guild = self.get_guild(payload.guild_id)

		# Make sure that the message the user is reacting to is the one we care about.
		message_relevant = False
		for category in self.data["servers"][str(guild.id)]["roles"]["category list"]:
			if payload.message_id == self.data["servers"][str(payload.guild_id)]["roles"]["category list"][category]["message id"]:
				message_relevant = True
				break
		if message_relevant is False:
			return

		# Make sure the user isn't the bot.
		if payload.member.id == self.user.id:  # was payload.author
			return

		# Check if we're still in the guild and it's cached.
		if guild is None:
			return

		# If the emoji isn't the one we care about then delete it and exit as well.
		role_id = -1
		for category in self.data["servers"][str(guild.id)]["roles"]["category list"]:  # For category in list
			for role in self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"]:  # For role in category
				if self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"][role]["emoji"] == str(payload.emoji):
					role_id = int(role)
					break
		if role_id == -1:
			# Not very efficient... comes from (https://stackoverflow.com/questions/63418818/python-discord-bot-python-clear-reaction-clears-all-reactions-instead-of-a-s)
			channel = await self.fetch_channel(payload.channel_id)
			message = await channel.fetch_message(payload.message_id)
			reaction = discord.utils.get(message.reactions, emoji=payload.emoji.name)
			await reaction.remove(payload.member)

			return

		# Make sure the role still exists and is valid.
		role = guild.get_role(role_id)
		if role is None:
			return

		# Finally, add the role.
		try:
			await payload.member.add_roles(role)
			logger.info("Role `" + role.name + "` added to " + payload.member.name)  # Event log

		# If we want to do something in case of errors we'd do it here.
		except discord.HTTPException:
			logger.error("Exception: discord.HTTPException. Could not add role " + role.name + " to " + payload.member.name)  # Event log

	async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
		"""Removes a role based on a reaction emoji."""

		guild = self.get_guild(payload.guild_id)

		# Make sure that the message the user is reacting to is the one we care about.
		message_relevant = False
		for category in self.data["servers"][str(guild.id)]["roles"]["category list"]:
			if payload.message_id == self.data["servers"][str(payload.guild_id)]["roles"]["category list"][category]["message id"]:
				message_relevant = True
				break
		if message_relevant is False:
			return

		# The payload for `on_raw_reaction_remove` does not provide `.member`
		# so we must get the member ourselves from the payload's `.user_id`.

		# Make sure the member still exists and is valid.
		member = guild.get_member(payload.user_id)
		if member is None:
			return

		# Make sure the user isn't the bot.
		if member.id == self.user.id:
			return

		# Check if we're still in the guild and it's cached.
		if guild is None:
			return

		# If the emoji isn't the one we care about then exit as well.
		role_id = -1
		for category in self.data["servers"][str(guild.id)]["roles"]["category list"]:  # For category in list
			for role in self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"]:  # For role in category
				if self.data["servers"][str(guild.id)]["roles"]["category list"][category]["role list"][role]["emoji"] == str(payload.emoji):
					role_id = int(role)
					break
		if role_id == -1:
			return

		# Make sure the role still exists and is valid.
		role = guild.get_role(role_id)
		if role is None:
			return

		# Finally, remove the role.
		try:
			await member.remove_roles(role)
			logger.info("Role `" + role.name + "` removed from " + member.name)  # Event log

		# If we want to do something in case of errors we'd do it here.
		except discord.HTTPException:
			logger.error("Exception: discord.HTTPException. Could not remove role " + role.name + " from ", member.name)  # Event log


# Main body
try:
	intents = discord.Intents.default()
	intents.members = True

	client = MyClient(intents=intents, debug=True)
	client.run(DISCORD_TOKEN)

	logger.info("That's all\n")  # Event log
except:

	# This is intended to catch all unexpected shutdowns and put a newline in the log file, since otherwise it becomes concatenated and horrible... Does on_kill exist?
	logger.error("Unexpected exception... Say that ten times fast\n")  # Event log
