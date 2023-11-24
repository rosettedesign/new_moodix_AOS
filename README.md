**Please be advised that the Moodix AOS software is strictly intended for educational and research purposes only. It is not designed nor authorized for live trading activities. Any attempt to use Moodix AOS for live or real-time trading is at the user’s own risk and the developers or distributors of Moodix AOS will not be held responsible for any financial loss or discrepancies that may occur as a result.**

# new_moodix_AOS
Description:
This code is designed for automated trading using the Interactive Brokers (IB) platform and retrieving market sentiment from the Moodix API. The code monitors the current market sentiment and tries to open a trade based on moving averages accordingly.

Features:
- Connects to Interactive Brokers via API.
- Retrieves market sentiment from the Moodix API.
- Automatically selects a trading instrument based on account size.
- Automatically opens trades based on moving averages and market sentiment.

How to Use:
- Run the code.
- Input your email and password for the Moodix API.
- The program will automatically monitor market sentiment and open trades.

## Installation
### Ubuntu 22.04 / WSL2 (default) on Windows
```
# Install the needed system packages
apt install -y python3 git

# Checkout the code
git clone https://github.com/rosettedesign/new_moodix_AOS.git

# Enter the code folder
cd new_moodix_AOS

# Install all Python packages
pip3 install -r requirements.txt

# Run the code
python3 connect.py
```
