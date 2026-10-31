import os
import random
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Fetch bot token from environment variables
TOKEN = os.getenv("BOT_TOKEN")

# In-memory database storing balances and user stats
user_balances = {}
user_spins = {}

START_BALANCE = 1000

def get_balance(user_id: int) -> int:
    return user_balances.get(user_id, START_BALANCE)

def set_balance(user_id: int, amount: int):
    user_balances[user_id] = amount

# Main menu keyboard generator
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🎰 Slots", callback_data="game_slots"),
            InlineKeyboardButton("🎲 Dice", callback_data="game_dice"),
        ],
        [
            InlineKeyboardButton("🪙 Coin Flip", callback_data="game_coinflip"),
            InlineKeyboardButton("💰 Balance", callback_data="menu_balance"),
        ],
        [
            InlineKeyboardButton("🚀 Boost Channel", callback_data="menu_boost"),
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="menu_bonus"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# /start command handler
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in user_balances:
        user_balances[user.id] = START_BALANCE
    
    welcome_text = (
        f"👋 Welcome to the Casino Bot, {user.first_name}!\n\n"
        f"💰 Starting Balance: **{get_balance(user.id)} coins**\n\n"
        "Choose an option below to play games or boost your balance:"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=main_menu_keyboard(), parse_mode="Markdown")

# Callback query router
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data

    if data == "menu_main":
        await start_command(update, context)

    elif data == "menu_balance":
        balance = get_balance(user_id)
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            f"💳 **Your Account Balance:**\n\n💰 `{balance}` coins",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "menu_boost":
        keyboard = [
            [InlineKeyboardButton("🚀 Boost Our Channel", url="https://t.me/boost")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]
        ]
        boost_text = (
            "🚀 **Boost Our Channel to Win Big!**\n\n"
            "Boost our Telegram channel to unlock VIP perks, higher rewards, and free daily spins!\n\n"
            "Click the button below to give us a boost."
        )
        await query.edit_message_text(boost_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "menu_bonus":
        # Simple daily reward claiming logic
        balance = get_balance(user_id)
        reward = 250
        set_balance(user_id, balance + reward)
        keyboard = [[InlineKeyboardButton("🔙 Back to Main Menu", callback_data="menu_main")]]
        await query.edit_message_text(
            f"🎁 **Daily Reward Claimed!**\n\nYou received **+{reward} coins**!\nNew Balance: `{get_balance(user_id)}` coins.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "game_slots":
        balance = get_balance(user_id)
        bet = 50
        if balance < bet:
            await query.edit_message_text("❌ You don't have enough balance! (Requires 50 coins)", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]]))
            return

        symbols = ["🍋", "🍒", "7️⃣", "🔔", "💎"]
        reel1, reel2, reel3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        
        if reel1 == reel2 == reel3:
            winnings = bet * 10
            set_balance(user_id, balance + winnings)
            result_msg = f"🎉 **JACKPOT!** You won `{winnings}` coins!"
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            winnings = bet * 2
            set_balance(user_id, balance + winnings)
            result_msg = f"✨ **MATCH!** You won `{winnings}` coins!"
        else:
            set_balance(user_id, balance - bet)
            result_msg = f"❌ No match. You lost `{bet}` coins."

        keyboard = [
            [InlineKeyboardButton("🎰 Play Again (-50)", callback_data="game_slots")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text(
            f"🎰 **SLOT MACHINE** 🎰\n\n[ {reel1} | {reel2} | {reel3} ]\n\n{result_msg}\n\n💰 New Balance: `{get_balance(user_id)}` coins",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "game_dice":
        balance = get_balance(user_id)
        bet = 50
        if balance < bet:
            await query.edit_message_text("❌ Insufficient balance!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]]))
            return

        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        
        if user_roll > bot_roll:
            winnings = bet * 2
            set_balance(user_id, balance + winnings)
            res = f"🎉 **You Won!** (+{winnings} coins)"
        elif user_roll < bot_roll:
            set_balance(user_id, balance - bet)
            res = f"❌ **You Lost!** (-{bet} coins)"
        else:
            res = "👔 **It's a Draw!** Bet refunded."

        keyboard = [
            [InlineKeyboardButton("🎲 Roll Again (-50)", callback_data="game_dice")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text(
            f"🎲 **DICE ROLL** 🎲\n\n🎲 You rolled: `{user_roll}`\n🎲 House rolled: `{bot_roll}`\n\n{res}\n\n💰 New Balance: `{get_balance(user_id)}` coins",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "game_coinflip":
        balance = get_balance(user_id)
        bet = 50
        if balance < bet:
            await query.edit_message_text("❌ Insufficient balance!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]]))
            return

        outcome = random.choice(["Heads", "Tails"])
        user_choice = random.choice(["Heads", "Tails"])
        
        if outcome == user_choice:
            winnings = bet * 2
            set_balance(user_id, balance + winnings)
            res = f"🎉 Coin landed on **{outcome}**! You won `{winnings}` coins!"
        else:
            set_balance(user_id, balance - bet)
            res = f"❌ Coin landed on **{outcome}**! You lost `{bet}` coins."

        keyboard = [
            [InlineKeyboardButton("🪙 Flip Again (-50)", callback_data="game_coinflip")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text(
            f"🪙 **COIN FLIP** 🪙\n\nYour pick: `{user_choice}`\n{res}\n\n💰 New Balance: `{get_balance(user_id)}` coins",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable not set.")
    
    # Disable job_queue to avoid the weakref crash on Python 3.13
    app = Application.builder().token(TOKEN).job_queue(None).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    
    logger.info("Starting Telegram Casino Bot...")
    app.run_polling()

if __name__ == "__main__":
    main()
