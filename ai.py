import discord
from discord.ext import commands
from ollama import Client
from duckduckgo_search import DDGS
import asyncio
import io

# --- CONFIGURATION ---
TOKEN = 'YOUR TOKEN'
MODEL = 'YOUR MODEL'
ollama_client = Client(host='http://127.0.0.1:11434')

SYSTEM_PROMPT = (
YOUR SYS PROMPT
)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

user_context = {}

def get_web_results(query):
    """SEARCH ON DUCKDUCKGO"""
    try:
        with DDGS() as ddgs:
            # 10 risultati sono ottimi per Moondream che ha buona memoria
            search_results = [r['body'] for r in ddgs.text(query, max_results=10)]
            return "\n".join(search_results)
    except Exception as e:
        print(f"Search error: {e}")
        return ""

@bot.event
async def on_ready():
    print(f'--- Bot Online as {bot.user} ---')
    print(f'Ready on PC with {MODEL} (Vision Enabled)')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Risponde nei DM o se menzionato
    if isinstance(message.channel, discord.DMChannel) or bot.user.mentioned_in(message):
        async with message.channel.typing():
            uid = message.author.id
            user_input = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()

            image_data = None
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']):
                        image_data = await attachment.read()
                        print(f"photo received: {attachment.filename}")
                        break

            if not user_input and not image_data:
                return

            if uid not in user_context:
                user_context[uid] = [{'role': 'system', 'content': SYSTEM_PROMPT}]

            # if there is text, we do a search
            web_info = ""
            if user_input:
                print(f"Searching web for: {user_input}")
                web_info = get_web_results(user_input)
            
            # prepare the text for ollama
            content = f"WEB CONTEXT (MARCH 2026):\n{web_info}\n\nUSER QUESTION: {user_input if user_input else 'Descrivi questa immagine'}"
            
            msg_obj = {'role': 'user', 'content': content}
            if image_data:
                msg_obj['images'] = [image_data]

            user_context[uid].append(msg_obj)

            try:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, lambda: ollama_client.chat(
                    model=MODEL, 
                    messages=user_context[uid],
                    keep_alive='1m' # Libera la RAM dopo 1 minuto per Windows 10
                ))
                
                answer = response['message']['content']
                user_context[uid].append({'role': 'assistant', 'content': answer})

                # cleaning memory for 8GB RAM
                if len(user_context[uid]) > 5:
                    user_context[uid] = [user_context[uid][0]] + user_context[uid][-4:]

                # answer
                if len(answer) > 2000:
                    for i in range(0, len(answer), 2000):
                        await message.reply(answer[i:i+2000])
                else:
                    await message.reply(answer)

            except Exception as e:
                await message.reply("⚠️ Ollama connection error. Make sure it's active!")
                print(f"Error: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)