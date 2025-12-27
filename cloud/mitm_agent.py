import os
import argparse



# Setup argument parser
parser = argparse.ArgumentParser(description='Local Mitm Agent')
parser.add_argument('--idx', type=int, default=1, help='Agent index (default: 1)')
args = parser.parse_args()

current_agent_idx = args.idx


os.system(f'mitmdump -s intercept_requests.py -p 850{current_agent_idx}')
# Note: The port number is dynamically set based on the agent index.