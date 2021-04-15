'''
Created on Apr 12, 2021

@author: wizen
'''


#Import libraries of commands for easy use.    
import os
import discord
import mysql.connector
from discord.ext import commands
from discord.utils import get

# load libraries to handle .env file
from dotenv import load_dotenv
# load the .env file
load_dotenv()
    
# set discord intents, set purpose for bot. 
# administrative but necessary.
# load a default set then members permissions in addition
# This is what lets us find members by member id
intents = discord.Intents.default()
intents.members = True

# set up the bot
bot = commands.Bot(command_prefix='!')

# define authentication token & db password.
TOKEN = os.getenv('DISCORD_TOKEN')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# set up the database handler
mydb = mysql.connector.connect(
  host="localhost",
  user="redbeardRoles",
  password=DB_PASSWORD,
  database="redbeardRoles"
)
#set up the mysql query handler
sql=mydb.cursor()

#(My Simple Query Language, free version of MSSQL, just guess what MS means)

 
#define async event, asynchronous means any function can be called in any order, or not at all.
@bot.event
async def on_ready():
    #do stuff when bot is ready, only runs once on bot startup.
    print("Bot ready!")

@bot.event
async def on_raw_reaction_add(ctx):
    # send query to db server & retrieve it
    reactionAddQuery = sql.execute('select role_id from savedTriggers where reactcode = "'+ str(ctx.emoji) +'" and message_id = '+ str(ctx.message_id) +';')
    roleToAdd = sql.fetchone()
    
    # fetch role from guild role list
    thisGuild = get(bot.guilds, id=ctx.guild_id)
    thisRole = get(await thisGuild.fetch_roles(), id=roleToAdd[0])

    # if person reacting is not the bot, assign role.
    if ctx.member.id != bot.user.id:
        await ctx.member.add_roles(thisRole)
    
@bot.event
async def on_raw_reaction_remove(ctx):
#   remove from thisMember the result of query (select role from savedTriggers where message_id = message_id and reaction = emoji)
    # query server for the reaction removed & fetch result
    reactcodeQuery = sql.execute('select reactcode from savedTriggers where message_id = "'+str(ctx.message_id)+'";')
    reactcode = sql.fetchone()
    
    if reactcode:
         #Remove the role for ctx.emoji and ctx.message_id
        thisGuild = get(bot.guilds, id=ctx.guild_id)
        theseMembers =  await thisGuild.query_members(limit=1, user_ids=ctx.user_id, cache=True)
        thisMember = get(theseMembers, id=ctx.user_id)
        roleQuery = sql.execute('select role_id from savedTriggers where reactcode = "'+ str(ctx.emoji) +'" and message_id = '+ str(ctx.message_id) +';')
        rightRole = sql.fetchone()
        thisRole = get(await thisGuild.fetch_roles(), id=rightRole[0])
        try:
            await thisMember.remove_roles(thisRole)
        except Exception as e:
            print("Exception in raw_reaction_remove: " + str(e))

@bot.event
async def on_message(ctx):
    #Note "ctx" and all the things that rely on it.
    #on_message's ctx is an instance of type Message, which is a class of object in discord.py
    #that's object as in Object Oriented Programming. Programming oriented around making 
    #stuff easy with recursive object memberships.
    #this language is python, the indenting is not only visually appealing, it is
    #also part of the syntax, or the rules of the language.
    
    # https://discordpy.readthedocs.io/en/latest/api.html?highlight=message#discord.Message
    # that is the URL for the documentation of discord.py Application Programming Interface (API)
    # Explains the attributes (ctx.channel in this case is the channel the message came in, for example)
    # explains the methods (like attribute but they do stuff instead of just being there)
    # notice how in raw_reaction_remove above we use ctx.remove_reaction()
    
    # each function definition "passes" its own "arguments" (gives a different ctx version)
    #and  ctx could be called anything, ctx is just short for context and it's used in the context
    # of the definition, so you see ctx used throughout just 'cuz it's my form./
    
    #If message is command
    if ctx.content.startswith('!') and len(ctx.content)>1 and ctx.author.bot == False:
        #And if the user is admin
        if ctx.author.guild_permissions.administrator:
            # Take the command prefix off the string & split into a list by string whitespace
            msg = ctx.content[1:].split()
            
            #Do various commands. More can be added later.
            if msg[0] == "rbrhelp": 
                #Just sends a message.
                await ctx.channel.send("Adding a reaction (admins only!): !rbradd messageID emoji roleID")
            if msg[0] == "rbradd":
                # "good" commands have 4 arguments. "rbradd", message_id, emoji, role_id
                if len(msg) != 4:
                    #4 is the number of counting
                    #The number of counting shall be 4
                    #If 5 arguments, that's too many
                    #6 is right out 
                    await ctx.channel.send("Wrong number of arguments! !rbrhelp for syntax.")
                    return # <--- this stops any further ifs from being checked. over 4 is right out. Under 4 is right out. 4 is the good number.
                #put results of splitting string into human readable forms
                thisMessageID = msg[1]
                thisEmoji = msg[2]
                thisRoleID = msg[3]
                #Arbitrary query to see if we have this message in the db already
                msgQuery = sql.execute('select _index from savedTriggers where message_id = "'+str(ctx.id)+'";')
                msgIsWatched = sql.fetchall()
                #If we find a record with the message_id
                #Basically asking "Is this a thing?"
                if msgIsWatched: 
                    #It's a thing. Do stuff to the thing.
                    await ctx.channel.send("Adding emoji to watched message...")
                    
                    #means what it says. tries a thing, braces itself for an error.
                    #if error is found, you can handle it without the bot crashing
                    try:
                        sql.execute('insert into savedTriggers (message_id,reactcode,role_id) values ('+str(thisMessageID)+',"'+str(thisEmoji)+'","'+str(thisRoleID)+'");')
                        mydb.commit()
                    except Exception as e:
                        print("Existing Message Exception:" + str(e))
                    #Things to do ONLY IF except wasn't called.
                    finally:
                        ctx.add_reaction(thisEmoji)
                        ctx.channel.send("Emoji added to existing watched message.")
                #It's not a thing, so no record was found.
                #Create new record.
                else:
                    try:#           INSERT INTO tableName (field_1, field_2, field_3) VALUES (value_1, value_2, value_3) 
                        #           the + concatenates, or sticks together, two strings. str(variablename) hot converts contents to string.
                        #           That both sql and python require quotes for syntax makes things look confusing
                        #           python accepts " or ' while sql requires ". keeping this in mind one can make sense of the statements.
                        sql.execute('INSERT INTO savedTriggers (message_id,reactcode,role_id) VALUES (' + str(thisMessageID) + ',"' + str(thisEmoji) + '",' + str(thisRoleID) + ');')
                        mydb.commit()
                    except Exception as e:
                        print("New Message Exception: "+str(e))
                    finally:
                        thisMessage = await ctx.channel.fetch_message(thisMessageID)
                        await thisMessage.add_reaction(thisEmoji)
                        await ctx.channel.send("Emoji added to new message.")   
            
            
        
        
# run the bot using the value in TOKEN for authentication.
bot.run(TOKEN)