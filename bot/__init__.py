import os
import logging
import discord
import aiohttp
import pickle
import openai

from datetime import datetime
from discord.ext import tasks
from dotenv import load_dotenv
from web3 import HTTPProvider
from ens import ENS

def main():
    load_dotenv()
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
    SENT_PROPOSALS_FILE = "sent_proposals.pkl"
    openai.api_key = os.getenv("GPT3_API_KEY")

    intents = discord.Intents.default()
    intents.typing = False
    intents.presences = False

    bot = discord.Client(intents=intents)

    provider = HTTPProvider("https://rpc.ankr.com/eth")
    ns = ENS(provider)

    # 2. Update 'lexdao.eth' to your space name on Snapshot
    QUERY = '''
    query Proposals {
      proposals (
        first: 20,
        skip: 0,
        where: {
          space_in: ["lexdao.eth"],            
          state: "active"
        },
        orderBy: "created",
        orderDirection: desc
      ) {
        id
        title
        body
        choices
        start
        end
        snapshot
        state
        author
        ipfs
        space {
          id
          name
        }
      }
    }
    '''

    def load_sent_proposals():
        try:
            with open(SENT_PROPOSALS_FILE, "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return set()

    def save_sent_proposals(sent_proposals):
        with open(SENT_PROPOSALS_FILE, "wb") as f:
            pickle.dump(sent_proposals, f)

    sent_proposals = load_sent_proposals()

    async def fetch_proposals():
        async with aiohttp.ClientSession() as session:
            async with session.post("https://hub.snapshot.org/graphql", json={"query": QUERY}) as response:
                data = await response.json()
                return data["data"]["proposals"]

    def ordinal_suffix(day):
        if 4 <= day <= 20 or 24 <= day <= 30:
            return "th"
        else:
            return ["st", "nd", "rd"][day % 10 - 1]

    def format_date(timestamp):
        dt = datetime.fromtimestamp(int(timestamp))
        day_suffix = ordinal_suffix(dt.day)
        return dt.strftime(f'%-d{day_suffix} %B, %Y %-I:%M %p')
    
    def format_ipfs(ipfs):
        return f"https://ipfs.io/ipfs/{ipfs}"

    async def resolve_ens_name(address):
        try:
            ens = ns.name(address)
            logging.warning(ens)
            if ens:
                return ens
            else:
                return address
        except Exception:
            return address

    async def generate_summary(text):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Please summarize the following text:\n\n{text}\n\nSummary:",
            temperature=0,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
        summary = response.choices[0].text.strip() # type: ignore 0_0
        return summary

    async def format_proposal_embed(proposal):
        proposal_link = f"https://snapshot.org/#/lexdao.eth/proposal/{proposal['id']}"
        ipfs_link = format_ipfs(proposal['ipfs'])
        
        start_time = format_date(proposal['start'])
        end_time = format_date(proposal['end'])
       
        author = await resolve_ens_name(proposal['author'])
        summary = await generate_summary(proposal['body'])
        
        embed = discord.Embed(
            title=proposal['title'], url=proposal_link, color=0x7CFC00)  # Green
        embed.add_field(name="Author", value=author, inline=False)
        embed.add_field(name="TL;DR by AI", value=summary, inline=False)
        embed.add_field(name="Started", value=start_time, inline=True)
        embed.add_field(name="Ends", value=end_time, inline=True)
        embed.add_field(name="Choices", value=', '.join(
            proposal['choices']), inline=True)
        embed.add_field(name="IPFS", url=ipfs_link, color=0x0000FF, inline=True)
        return embed

    async def send_proposal_message(channel, embed):
        await channel.send(embed=embed)

    @tasks.loop(minutes=1)
    async def check_new_proposals():
        proposals = await fetch_proposals()
        channel = bot.get_channel(CHANNEL_ID)
        for proposal in proposals:
            if proposal["id"] not in sent_proposals:
                embed = await format_proposal_embed(proposal)
                await send_proposal_message(channel, embed)
                sent_proposals.add(proposal["id"])
                save_sent_proposals(sent_proposals)

    @bot.event
    async def on_ready():
        print(f"{bot.user} has connected to Discord!")
        check_new_proposals.start()

    bot.run(TOKEN)
