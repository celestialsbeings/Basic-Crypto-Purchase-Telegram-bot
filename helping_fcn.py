import random 
import string 
from datetime import datetime
from dateutil.relativedelta import relativedelta


def sec_key(length=16):
    # Use only alphanumeric characters and a few selected symbols
    safe_characters = string.ascii_letters + string.digits + "-_"
    key = ''.join(random.choice(safe_characters) for _ in range(length))
    return "CRYPTO" + key



def saveid(user_id):
    filename = "userid.txt"
    user_id = str(user_id)
    # Open the file and read all lines into a list
    try:
        with open(filename, "r") as file:
            existing_ids = file.read().splitlines()
    except FileNotFoundError:
        existing_ids = []

    # If the user_id is not already in the file, append it
    if user_id not in existing_ids:
        with open(filename, "a") as file:
            file.write(user_id + "\n")

def check_root(user_id):
    user_id = str(user_id)
    try:
        with open("root.txt","r") as f:#fcn for checking userid in root file to verify user in before using specific commmand 
            lines = f.read().splitlines()
            return user_id in lines 
            
    except FileNotFoundError:
        return False
    
def claiming_key(enterkey, user_id, username):
    current_date = datetime.now().date()
    new_date = None
    duration = None
    time = None

    # Read all lines from the file
    with open("key.txt", "r") as f:
        lines = f.readlines()

    # Open the file in write mode to overwrite it
    with open("key.txt", "w") as f:
        for line in lines:
            line_duration, line_time, key = line.strip().split(",")
            if enterkey == key:
                duration = line_duration
                time = int(line_time)

                # Calculate the new date based on the duration
                if duration == "month":
                    new_date = current_date + relativedelta(months=time)
                elif duration == "year":
                    new_date = current_date + relativedelta(years=time)
                else:
                    return False, None, None, None
                
                # Save the subscription info to paid.txt
                with open("paid.txt", "a") as paid_file:
                    paid_file.write(f"{user_id},{username},{new_date}\n")

                
                continue  # Skip writing this line back to key.txt

            # Write all lines except the claimed one back to the file
            f.write(line)

    # Return True if a key was claimed, otherwise return False
    if duration:
        return True, new_date, duration, time
    else:
        return False, None, None, None



def checking_paid(user_id):
    current_date = datetime.now().date()  # Get the current date
    valid_lines = []  # List to store lines with valid subscriptions
    subscription_valid = False  # Flag to indicate if subscription is valid

    with open("paid.txt", "r") as file:
        lines = file.readlines()

    for line in lines:
        try:
            current_id_str, current_username, subs_date_str = line.strip().split(",")
            current_id = int(current_id_str)
            user_id = int(user_id)  # Ensure user_id is also an integer
            
            # Convert subscription date string to date object
            subs_date = datetime.strptime(subs_date_str, '%Y-%m-%d').date()

            if user_id == current_id:
                if subs_date >= current_date:
                    subscription_valid = True
                    valid_lines.append(line)  # Keep the valid subscription
                else:
                    continue
            else:
                valid_lines.append(line)  # Keep other valid subscriptions

        except ValueError as e:

            continue

    # Write valid subscriptions back to the file
    try:
        with open("paid.txt", "w") as file:
            file.writelines(valid_lines)
    except IOError:
        print("Error: Could not write to 'paid.txt' file.")
    
    return subscription_valid

def info(user_id):
    current_date = datetime.now().date()
    
    try:
        with open("paid.txt", "r") as f:
            lines = f.readlines()  # Read all lines from the file
            
        for line in lines:
            usrid, username, sub_date = line.strip().split(',')
            usrid = int(usrid)
            user_id = int(user_id)
            subs_date = datetime.strptime(sub_date, '%Y-%m-%d').date()  # Convert stored date to date object

            if user_id == usrid:
                if subs_date >= current_date:
                    return usrid, username, sub_date, "running"
                else:
                    return usrid, username, sub_date, "expired"
        
        # If the user ID is not found in the file
        return None, None, None, "no"
    
    except FileNotFoundError:
        # Handle the case where the file does not exist
        return None, None, None, "no"
    except Exception as e:
        # Handle other potential exceptions
        print(f"Error reading file: {e}")
        return None, None, None, "error"
    
# def showorder():
#     orders = []
#     with open("cc.txt","r") as f:
#         lines = f.readlines()
#         for line in lines:
#             data =  line.strip()   no need of this fcn now i am directly sending file to root 
#             orders.append(data)
#         return orders

            

def order_complete(usrname, amt):
    removed = False
    with open('cc.txt', 'r') as f:
        lines = f.readlines()

    with open('cc.txt', 'w') as f:
        for line in lines:
            usrid, username, amount, wallet, cc = line.strip().split(',')
            if usrname == username and amount == amt:
                removed = True
                continue  # Skip writing this line back to the file
            f.write(line + '\n')  # Write back all other lines

    return removed, usrid

                
                

            
            
# order_complete()

def broad():
    idss = []
    with open("userid.txt","r") as f:
        lines = f.readlines()
        for line in lines:
            id = line.strip()
            idss.append(id)
    return idss
        
    