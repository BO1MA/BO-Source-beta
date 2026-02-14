from setuptools import setup, find_packages

setup(
    name="telegram-group-bot",
    version="1.0.0",
    description="Arabic Telegram Group Management Bot",
    author="Ahmed",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "python-telegram-bot>=20.7",
        "redis>=5.0.0",
        "python-dotenv>=1.0.0",
        "aiohttp>=3.9.0",
        "yt-dlp>=2024.1.1",
    ],
    entry_points={
        "console_scripts": [
            "bot=src.bot:main",
        ],
    },
)
