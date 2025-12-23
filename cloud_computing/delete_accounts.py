import shutil
import os

def force_delete(path):
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
        print(f"Deleted: {path}")
    else:
        print("Path does not exist")

# Example:
force_delete(os.getcwd() + "\\accounts")  # Be cautious with this! It will delete the current working directory.
os.mkdir(os.getcwd() + "\\accounts")  # Recreate the directory for demonstration purposes.