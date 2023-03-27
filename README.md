# Chronos

Chronos bot is a Discord bot that automatically fetches and announces active proposals from a specified Snapshot space. It uses `text-davinci-003` to generate a summary for each proposal and includes relevant details such as author, timeline, and choices in a clean embed. It also resolves ENS names for authors and provides the IPFS link for the complete proposal.

## Features

- Fetch active proposals from a specified Snapshot space
- Generate a summary using OpenAI API
- Announce proposals in a specified Discord channel with a formatted embed
- Resolve ENS names for authors
- Provide IPFS link for the complete proposal

## Installation & Usage

### Prerequisites

- Python 3.8+
- Poetry (Python package manager)

### Setup

1. Clone the repository:

```
git clone https://github.com/lexDAO/chronos.git
```

2. Install dependencies using Poetry:

```
cd chronos
poetry install
```

3. Create a `.env` file in the project root directory with the following variables:

```
DISCORD_BOT_TOKEN=your_bot_token
DISCORD_CHANNEL_ID=your_channel_id
GPT3_API_KEY=your_gpt3_api_key
