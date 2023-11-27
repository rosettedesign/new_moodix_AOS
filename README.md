
# Moodix template - Automated Trading System Integration with Moodix API

## Disclaimer
Please be advised that the Moodix AOS software is strictly intended for educational and research purposes only. It is not designed nor authorized for live trading activities. Any attempt to use Moodix AOS for live or real-time trading is at the user’s own risk and the developers or distributors of Moodix AOS will not be held responsible for any financial loss or discrepancies that may occur as a result.

## new_moodix_AOS
**Description:** This code is designed for automated trading using the Interactive Brokers (IB) platform and retrieving market sentiment from the Moodix API. The code monitors the current market sentiment and tries to open a trade based on moving averages accordingly.

## Project Files

### `order.py`
This file contains functions for managing trading orders. Key functions include:
- `close_order(ib, order_id)`: Closes an order with the given ID.
- `is_bracket_order(order, ma_identifiers)`: Checks if an order is part of 'bracket' orders.

### `connect.py`
`connect.py` includes functions for connecting to and interacting with the Interactive Brokers platform. It contains functions such as:
- `install_requirements(file_path)`: Installs required libraries from the `requirements.txt` file.

### `requirements.txt`
Lists the Python libraries required for the proper functioning of the project.

## Installation
To install the project dependencies, use the following command:
```bash
pip install -r requirements.txt
```

## Usage
Include examples of how to use the functions from `order.py` and `connect.py` here.

## License
Include information about your project's license here, if applicable.

## Detailed Logic Explanation

The Moodix AOS project integrates with the Interactive Brokers (IB) platform for automated trading and incorporates market sentiment analysis through the Moodix API. Here's a detailed breakdown of the program's logic:

### 1. Connection and Setup
- **Interactive Brokers Integration**: The project uses `connect.py` to establish a connection with the IB platform. This involves setting up necessary parameters and ensuring a stable connection for executing trades.
- **Requirements Installation**: The `install_requirements` function in `connect.py` is used to install all the necessary Python libraries listed in `requirements.txt`, ensuring that all dependencies are met.

### 2. Order Management
- **Order Handling**: In `order.py`, the program provides functionalities to manage trading orders. This includes creating, modifying, and closing orders based on the trading strategy.
- **Close Order**: The `close_order` function is crucial for risk management, allowing the system to exit trades when specific criteria are met.
- **Bracket Order Checks**: The `is_bracket_order` function checks if an order is part of a group of orders (bracket orders) that are typically used for managing risks by setting pre-defined loss limits and profit targets.

### 3. Trading Logic
- **Market Sentiment Analysis**: The program interfaces with the Moodix API to retrieve market sentiment data. This data is likely used to gauge the overall mood of the market, which can be a critical factor in decision-making for trades.
- **Moving Average Strategy**: The code appears to utilize a strategy based on moving averages, a common technical analysis tool used to identify trends and potential entry/exit points in the market.
- **Trade Execution**: Based on the combination of market sentiment and moving average analysis, the program decides when to open or close trades. This decision-making process is automated, aligning with the principles of algorithmic trading.

### 4. Risk Management
- **Automated Controls**: The system likely incorporates automated risk management features, such as stop-loss orders, to protect against significant losses.
- **Monitoring and Adjustments**: Continuous monitoring of market conditions and adjusting strategies in real-time is an essential aspect of the system, ensuring adaptability to market changes.

## Trading Configuration Explanation

The trading logic of Moodix AOS is driven by a set of configuration parameters defined in the `config` dictionary. Here's what each key represents:

- `size_account`: This maps the account size to the type of instrument to be traded. For instance:
  - An account with $500 will trade 'SPY' assets.
  - An account with $20,000 will trade 'MES' futures.
  - An account with $200,000 will trade 'ES' futures.
  
- `leverage`: Indicates the leverage factor that can be applied in trading.

- `max_positions`: The maximum number of open positions that can be held concurrently.

- `max_ma`: The maximum moving average value used in the trading strategy.

- `min_difference`: The minimum price difference (in percentage) that must be met to consider a trading signal.

- `ma_configurations`: Specifies configurations for various levels of moving averages. Each MA level has a defined 'take_profit' and 'stop_loss' percentage, indicating target prices for profit realization and the level at which a position is closed to limit losses. The 'next' key indicates the subsequent MA to use, and 'distance' is the percentage gap from the current price to the target price.

These configurations dictate the trading behavior based on account size, leverage, the number of positions, and trading rules based on moving averages. It's a crucial part of the algorithm that adapts the trading strategy according to the financial capacity and risk profile of the account.


## Interactive Brokers API Configuration

To ensure proper communication with the Interactive Brokers (IB) platform, specific API settings must be configured as follows:

- **Enable ActiveX and Socket Clients**: This option should be checked to allow the API to connect through socket clients.
- **Read-Only API**: If checked, this option ensures the API has only the ability to read data and cannot execute trades.
- **Socket Port**: The default port is `7497` for paper trading accounts, which is typically used for development and testing.
- **Logging Level**: Set to `Error` to log only error messages, reducing the amount of logged information.
- **Master API Client ID**: Should be set to `1` unless multiple clients are connecting to the API simultaneously.
- **Timeout to send bulk data to API**: Set to `30` to define the timeout in seconds for sending bulk data requests to the API.

Ensure that all the settings match your specific requirements and the setup of your trading system.

## Platform Requirements

Before running the Moodix AOS, the following requirements must be met on the Interactive Brokers platform:

- **Platform Running**: The IB platform must be up and running with an active connection to the internet.
- **Data Subscriptions**: Subscriptions for market data must be active. For futures (e.g., /ES, MES) or CFDs (e.g., IBUS500), ensure you have the necessary subscriptions in place to receive real-time market data.
- **Trading Permissions**: Permissions for trading futures or CFDs must be granted on your IB account to allow the automated system to execute trades.

Please note that without these prerequisites, the Moodix AOS will not be able to function correctly.
