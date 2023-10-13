import time
from datetime import datetime
import base64
import requests
from ib_insync import IB, Stock, Future, util, Order
from ib_insync import MarketOrder
import logging
from ib_insync import util
import asyncio

# logovani
# util.logToConsole()
# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

# Globální seznam pro sledování otevřených obchodů a jejich klouzavých průměrů
open_trades = []

small_acc = 2000
mid_acc = 20000
big_acc = 200000

# Inicializace a připojení k IB
ib = IB()


try:
    ib.connect('127.0.0.1', 7497, clientId=1)  # IP, port, and clientId might be different based on your setup
except ConnectionRefusedError:
    print("Connection to Interactive Brokers refused. Please ensure TWS or IB Gateway is running and correctly configured.")
    exit()
except asyncio.exceptions.TimeoutError:
    print("Connection to Interactive Brokers timed out. Please check your connection and try again.")
    exit()

managed_accounts = ib.managedAccounts()
for account in managed_accounts:
    if account.startswith('DU'):
        print("Account type: Paper account")
    elif account.startswith('U'):
        print("Real account, not allowed!")



config = {
    'ma_configurations': {
        72: {'take_profit': 0.02, 'stop_loss': 0.01},  # 2% TP a 1% SL pro MA72
        144: {'take_profit': 0.03, 'stop_loss': 0.015},  # Příkladní hodnoty
        288: {'take_profit': 0.04, 'stop_loss': 0.02},  # Příkladní hodnoty
        720: {'take_profit': 0.05, 'stop_loss': 0.025},  # Příkladní hodnoty
    },
    'max_positions': 4,  # Maximální počet otevřených pozic
    # ... další konfigurační data ...
}

def ascii():
    print(" ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄  ▄▄▄ ▄▄   ▄▄ ")
    print(" █  █▄█  █       █       █      ██   █  █▄█  █ ")
    print(" █       █   ▄   █   ▄   █  ▄    █   █       █ ")
    print(" █       █  █ █  █  █ █  █ █ █   █   █       █ ")
    print(" █       █  █▄█  █  █▄█  █ █▄█   █   ██     █  ")
    print(" █ ██▄██ █       █       █       █   █   ▄   █ ")
    print(" █▄█   █▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄██▄▄▄█▄▄█ █▄▄█ ")
    print("..................................... ver. O.1")
    print("")
    print("")

ascii()
# Získání přihlašovacích údajů od uživatele
username = input("Zadejte vás e-mail : ")
password = input("Zadejte heslo: ")




def get_current_date_string():
    current_date = datetime.now()
    return current_date.strftime('%Y%m%d-23:00:00')


def get_market_sentiment(username, password):
    # Vytvoření Basic Auth řetězce
    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()

    print("Získávání informací o sentimentu trhu...")
    url = "https://app.moodix.market/api/moodix-stat/"
    payload = {}
    headers = {
        'Authorization': f'Basic {credentials}'
    }
    try:
        response = requests.request("GET", url, headers=headers, data=payload)
        data = response.json()

        # Extrahujeme sentiment a trend z dat
        sentiment = data['results'][0]['sentiment']
        trend = data['results'][0]['trend']

        return sentiment, trend

    except requests.exceptions.RequestException as e:
        print(f"Chyba spojení s moodix. Špatné jméno/heslo nebo nedostupná služba: {e}")
        return None


def select_instrument():
    print("Výběr nástroje pro obchodování...")
    # Získání informací o účtu
    account_infos = ib.accountSummary()

    # Extrahování hodnoty Currency a NetLiquidation
    currency = next((info.value for info in account_infos if info.tag == 'Currency'), None)
    net_liquidation = next((float(info.value) for info in account_infos if info.tag == 'NetLiquidation'), None)

    # Kontrola měny účtu
    if currency != 'USD':
        raise ValueError("Obchodovat lze pouze na USD účtu.")

    # Kontrola velikosti účtu a páky
    if net_liquidation < small_acc:
        raise ValueError("Minimální vklad je 5000$. Aktuální vklad je: " + str(net_liquidation))

    # Kontrola maximálního počtu otevřených pozic
    open_positions = len(ib.positions())
    if open_positions >= 4:
        raise ValueError(f"Maximum otevřených pozic je 4. Aktuálně máte {open_positions} otevřených pozic.")

    # Výběr instrumentu podle velikosti účtu
    if small_acc <= net_liquidation < mid_acc:
        return 'SPY'
    elif mid_acc <= net_liquidation < big_acc:
        return 'MES'
    else:
        return 'ES'


def get_moving_averages(instrument, duration, end_date):
    print(f"Získávání klouzavých průměrů pro {instrument}...")
    # Vytvoření objektu Contract na základě názvu instrumentu
    if instrument == 'SPY':
        contract = Stock('SPY', 'ARCA')
    elif instrument in ['MES', 'ES']:
        # Získání detailů kontraktu
        generic_contract = Future(instrument, exchange='CME')
        contracts = ib.reqContractDetails(generic_contract)

        if not contracts:
            raise ValueError(f"Nepodařilo se najít kontrakt pro {instrument} na CME.")

        # Seřazení kontraktů podle data expirace a výběr toho s nejbližším datem
        sorted_contracts = sorted(contracts, key=lambda x: x.contract.lastTradeDateOrContractMonth)
        contract = sorted_contracts[0].contract
    else:
        raise ValueError(f"Neznámý instrument: {instrument}")

    bars = ib.reqHistoricalData(
        contract,
        endDateTime=end_date,
        durationStr=duration,
        barSizeSetting='10 mins',
        whatToShow='TRADES',
        useRTH=False
    )
    if not bars:
        raise ValueError("Nepodařilo se získat historická data.")

    df = util.df(bars)

    for ma_period in config['ma_configurations'].keys():
        df[f'MA{ma_period}'] = df['close'].rolling(window=ma_period).mean()

    return df


def get_contract_for_instrument(instrument):
    print(f"Získávání kontraktu pro {instrument}...")
    if instrument == 'SPY':
        return Stock('SPY', 'ARCA')
    elif instrument in ['MES', 'ES']:
        generic_contract = Future(instrument, exchange='CME')
        contracts = ib.reqContractDetails(generic_contract)
        if not contracts:
            raise ValueError(f"Nepodařilo se najít kontrakt pro {instrument} na CME.")
        sorted_contracts = sorted(contracts, key=lambda x: x.contract.lastTradeDateOrContractMonth)
        return sorted_contracts[0].contract
    else:
        raise ValueError(f"Neznámý instrument: {instrument}")


def check_and_open_trade(df, sentiment, instrument):
    print(f"Kontrola a pokus o otevření obchodu s sentimentem {sentiment} na {instrument}...")

    main_order_count = get_main_order_count()
    max_main_orders = len(config['ma_configurations'])

    if main_order_count >= max_main_orders:
        print(f"Limit hlavních objednávek dosažen: {main_order_count}/{max_main_orders}. Žádné další objednávky nebudou otevřeny.")
        return

    for ma_period, ma_values in config['ma_configurations'].items():
        if ma_period in open_trades:
            continue

        ma_value = df[f'MA{ma_period}'].iloc[-1]
        current_price = df['close'].iloc[-1]

        # Kontrolní výpis
        print(f"Klouzavý průměr MA{ma_period}: {ma_value}")
        print(f"Aktuální cena: {current_price}")

        if sentiment == "RiskOn" and current_price > ma_value:
            # Otevření long pozice
            trade = place_limit_order('BUY', instrument, ma_period, ma_value, ma_values)
            if trade:
                open_trades.append(ma_period)

        elif sentiment == "RiskOff" and current_price < ma_value:
            # Otevření short pozice
            trade = place_limit_order('SELL', instrument, ma_period, ma_value, ma_values)
            if trade:
                open_trades.append(ma_period)


def round_to_quarter(value):
    return round(value * 4) / 4


def place_limit_order(action, instrument, ma_period, ma_value, ma_values):
    print(f"Vytváření {action} limitní objednávky pro {instrument} s klouzavým průměrem {ma_period}...")
    contract = get_contract_for_instrument(instrument)

    ma_value = round_to_quarter(ma_value)

    if action == 'BUY':
        stop_loss_price = round_to_quarter(ma_value * (1 - ma_values['stop_loss']))
        take_profit_price = round_to_quarter(ma_value * (1 + ma_values['take_profit']))
    else:  # SELL
        stop_loss_price = round_to_quarter(ma_value * (1 + ma_values['stop_loss']))
        take_profit_price = round_to_quarter(ma_value * (1 - ma_values['take_profit']))

    # Příprava objednávky
    bracket_order = ib.bracketOrder(
        action=action,
        quantity=1,
        limitPrice=ma_value,
        takeProfitPrice=take_profit_price,
        stopLossPrice=stop_loss_price,
        outsideRth=True
    )

    # Nastavení referenčního atributu na hlavní objednávku
    bracket_order.parent.orderRef = f"MA{ma_period}"

    # Umístění hlavní objednávky a připojených objednávek
    main_trade = ib.placeOrder(contract, bracket_order.parent)
    ib.placeOrder(contract, bracket_order.takeProfit)
    ib.placeOrder(contract, bracket_order.stopLoss)

    # Čekání na aktualizaci stavu objednávky
    for _ in range(10):  # Čekání až 10 sekund
        ib.sleep(1)  # Čekání 1 sekundu
        if main_trade.orderStatus.status in ['Submitted', 'Filled']:
            break

    if main_trade.orderStatus.status in ['Submitted', 'Filled']:
        print(f"Obchod {action} na {instrument} s klouzavým průměrem {ma_period} byl otevřen.")
        return main_trade
    else:
        print(f"Obchod {action} na {instrument} s klouzavým průměrem {ma_period} nebyl otevřen.")
        return None


def place_order(action, instrument, ma_period, ma_values):
    print(f"Vytváření {action} objednávky pro {instrument} s klouzavým průměrem {ma_period}...")
    contract = get_contract_for_instrument(instrument)
    last_price = ib.reqTickers(contract)[0].marketPrice()

    if action == 'BUY':
        stop_loss_price = last_price * (1 - ma_values['stop_loss'])
        take_profit_price = last_price * (1 + ma_values['take_profit'])
    else:  # SELL
        stop_loss_price = last_price * (1 + ma_values['stop_loss'])
        take_profit_price = last_price * (1 - ma_values['take_profit'])

    order = MarketOrder(action, 1, outsideRth=True, tif='GTC')
    order.attachStopLoss(stopLossPrice=stop_loss_price)
    order.attachTakeProfit(takeProfitPrice=take_profit_price)

    trade = ib.placeOrder(contract, order)

    if trade.orderStatus.status == 'Filled':
        open_trades.append(ma_period)
        print(f"Obchod {action} na {instrument} s klouzavým průměrem {ma_period} byl otevřen.")
    else:
        print(f"Obchod {action} na {instrument} s klouzavým průměrem {ma_period} nebyl otevřen.")

    return trade


def get_open_positions_on_mas():
    open_positions = ib.positions()
    ma_positions = [int(pos.orderRef[2:]) for pos in open_positions if 'MA' in pos.orderRef]
    return ma_positions


def get_main_order_count():
    orders = ib.openOrders()
    main_orders = [order for order in orders if order.orderRef and order.orderRef.startswith('MA')]
    return len(main_orders)

# Hlavní smyčka
print("Spouštím hlavní smyčku...")
while True:
    try:
        sentiment, trend = get_market_sentiment(username, password)
        print(f"Aktuální sentiment: {sentiment}, trend: {trend}")
        if sentiment is None:
            print("Nepodařilo se načíst sentiment. Čekám na další pokus.")
            time.sleep(60)
            continue

        instrument = select_instrument()
        print(f"Vybraný nástroj pro obchodování: {instrument}")
        end_date = get_current_date_string()
        df = get_moving_averages(instrument, '7 D', end_date)
        check_and_open_trade(df, sentiment, instrument)

        # Počkejte 60 sekund před dalším během smyčky
        print("Čekám 5 sekund před dalším cyklem...")
        time.sleep(5)
    except Exception as e:
        print(f"Chyba při komunikaci s brokerem: {e}")
        time.sleep(60)
