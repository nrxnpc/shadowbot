BOT_TOKEN = '******'
DEPOSIT_ADDRESS = '*****'
API_KEY = '*****'
RUN_IN_MAINNET = True  # True для mainnet, False для testnet
ADMIN_ID = ***  # Ваш Telegram user ID без кавычек

if RUN_IN_MAINNET:
    API_BASE_URL = 'https://toncenter.com'
else:
    API_BASE_URL = 'https://testnet.toncenter.com'