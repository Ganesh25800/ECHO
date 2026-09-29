
def take_user_concern(speak):

    terminal_input = input("Do You Want To Share Your Details With Me (y/n): ").lower()

    if terminal_input == "n":
        return "denied"
    elif terminal_input == "y":
        return "agree"
    else:
        speak.speak("I didn't quite get that. If you'd like to share your details, press Y and Enter. Otherwise, press N and Enter.")
        return "wrong input"