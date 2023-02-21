import argparse
import sys
import os
from chatgpt_batch_whipper.pub.chatgpt_wrapper import ChatGPT
from chatgpt_batch_whipper.version import __version__
import cmd

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"{sys.argv[0]} version {__version__}",
        help="Print version and exit.",
    )
    parser.add_argument(
        "params",
        nargs="*",
        help="Use 'auth' for auth mode, or run 'ui' to start the streamlit UI.",
    )

    args = parser.parse_args()
    auth_mode = (len(args.params) == 1 and args.params[0] == "auth") or len(args.params) == 0
    run_mode = len(args.params) == 1 and args.params[0].upper() == "UI"

    if auth_mode:
        ChatGPT(headless=False, timeout=90)
    if run_mode:
        os.system("streamlit run start_whipper.py")
    else:
        print("please input the right command. Use 'auth' for auth mode, or run 'UI' to start the streamlit UI.")

    while True:
        choice = input("Enter Q to quit, or press return to continue")
        if choice.upper() == "Q":
            break


if __name__ == "__main__":
    main()