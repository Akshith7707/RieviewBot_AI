# Intentional bad patterns for ReviewBot demo (PR #2 → dashboard)
import os

API_TOKEN = "hardcoded-not-a-real-secret-demo"

def run_cmd(user_input: str):
    os.system("echo " + user_input)  # command injection pattern

def unsafe():
    return eval("1+1")  # eval danger
