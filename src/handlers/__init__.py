"""
Handler registration — imports all handler modules and provides
a single register_all_handlers() function for bot.py to call.
"""
from telegram.ext import Application

from . import (
    start, admin, moderation, broadcast, games, tag, locks,
    permissions, youtube, fun, dm_relay, custom_commands,
    user_info, auto_response, group_settings, misc_commands,
    maintenance,
    notifications,
)


def register_all_handlers(app: Application) -> None:
    """Register every handler module with the Application."""
    # Notifications first (low group number for priority)
    notifications.register(app)
    maintenance.register(app)
    
    start.register(app)
    admin.register(app)
    moderation.register(app)
    broadcast.register(app)
    games.register(app)
    tag.register(app)
    locks.register(app)
    permissions.register(app)
    youtube.register(app)
    fun.register(app)
    dm_relay.register(app)
    custom_commands.register(app)
    user_info.register(app)
    auto_response.register(app)
    group_settings.register(app)
    misc_commands.register(app)

    # Register economy system handlers
    from src.economy.handlers import register_economy_handlers
    from src.economy.admin import register_economy_admin
    register_economy_handlers(app)
    register_economy_admin(app)
