import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# In-memory database (User ID -> {"balance": int, "claimed": bool})
# Replace with PostgreSQL/Redis for persistent storage in production
USER_DATA = {}

START_BALANCE = 1000
DAILY_BONUS = 500

def get_user_data(user_id: int) -> dict:
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {"balance": START_BALANCE, "claimed": False}
    return USER_DATA[user_id]


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = get_user_data(user.id)
    
    keyboard = [
        [
            InlineKeyboardButton("🎰 Slots (Bet 100)", callback_data="play_slots"),
            InlineKeyboardButton("🎲 Dice (Bet 100)", callback_data="play_dice"),
        ],
        [
            InlineKeyboardButton("🪙 Coin Flip (Bet 100)", callback_data="play_coin"),
            InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus"),
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="get_balance"),
            InlineKeyboardButton("⚡ Boost Telegram Channel", url="https://t.me/telegram"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"👋 Welcome to Casino Boost, **{user.first_name}**!\n\n"
        f"💵 **Starting Balance:** `{data['balance']}` coins\n\n"
        "Choose a game below to play and boost your score!"
    )
    
    if update.message:
        await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = get_user_data(user_id)
    bet = 100

    if query.data == "get_balance":
        text = f"💳 Your current balance is: **{data['balance']}** coins."
        
    elif query.data == "daily_bonus":
        if not data["claimed"]:
            data["balance"] += DAILY_BONUS
            data["claimed"] = True
            text = f"🎁 You claimed your daily bonus of **{DAILY_BONUS}** coins! New balance: **{data['balance']}**."
        else:
            text = "❌ You have already claimed your bonus today!"

    elif query.data in ["play_slots", "play_dice", "play_coin"]:
        if data["balance"] < bet:
            text = f"❌ Insufficient funds! You need at least `{bet}` coins to play. Claim your daily bonus!"
        else:
            if query.data == "play_slots":
                symbols = ["🎰", "🍋", "🔔", "💎", "7️⃣"]
                res = [random.choice(symbols) for _ in range(3)]
                display = " | ".join(res)
                
                if res[0] == res[1] == res[2]:
                    win = bet * 5
                    data["balance"] += win
                    text = f"🎰 **{display}**\n\n🎉 **JACKPOT!** You won `{win}` coins! Balance: `{data['balance']}`"
                elif res[0] == res[1] or res[1] == res[2] or res[0] == res[2]:
                    win = bet * 2
                    data["balance"] += win
                    text = f"🎰 **{display}**\n\n✨ **MATCH 2!** You won `{win}` coins! Balance: `{data['balance']}`"
                else:
                    data["balance"] -= bet
                    text = f"🎰 **{display}**\n\n💔 No match. Lost `{bet}` coins. Balance: `{data['balance']}`"

            elif query.data == "play_dice":
                player_roll = random.randint(1, 6)
                bot_roll = random.randint(1, 6)
                
                if player_roll > bot_roll:
                    win = bet * 2
                    data["balance"] += win
                    text = f"🎲 You rolled **{player_roll}**, Bot rolled **{bot_roll}**.\n\n🎉 You WON `{win}` coins! Balance: `{data['balance']}`"
                elif player_roll < bot_roll:
                    data["balance"] -= bet
                    text = f"🎲 You rolled **{player_roll}**, Bot rolled **{bot_roll}**.\n\n💔 You LOST `{bet}` coins. Balance: `{data['balance']}`"
                else:
                    text = f"🎲 Both rolled **{player_roll}**.\n\n🤝 It's a DRAW! Balance returned: `{data['balance']}`"

            elif query.data == "play_coin":
                outcome = random.choice(["Heads", "Tails"])
                user_choice = random.choice(["Heads", "Tails"])
                
                if user_choice == outcome:
                    win = int(bet * 1.5)
                    data["balance"] += win
                    text = f"🪙 Coin landed on **{outcome}**!\n\n🎉 You won `{win}` coins! Balance: `{data['balance']}`"
                else:
                    data["balance"] -= bet
                    text = f"🪙 Coin landed on **{outcome}**!\n\n💔 You lost `{bet}` coins. Balance: `{data['balance']}`"

    keyboard = [
        [InlineKeyboardButton("🔙 Main Menu", callback_data="main_menu")],
    ]
    await query.message.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))


async def main_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start_command(update, context)


def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN environment variable not set!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(main_menu_handler, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(button_handler))

    logging.info("Bot starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
