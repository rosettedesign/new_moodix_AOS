import time
from ib_insync import IB, Future, util
from collections import defaultdict
from ib_insync import IB, Future
from datetime import datetime
from ib_insync import IB, Future
from datetime import datetime, timedelta, timezone
from ib_insync import Stock
import pprint
import pandas as pd
import base64
import requests
from collections import defaultdict
import re
from collections import defaultdict
import re

# Globální seznam pro sledování otevřených obchodů a jejich klouzavých průměrů
open_trades = []

config = {
    'size_account': {
        500: {'type': 'SPY'},
        20000: {'type': 'MES'},
        200000: {'type': 'ES'}
    },
    'leverage': 4,
    'max_positions': 4,
    'min_difference': 0.1, # v procentech
    'ma_configurations': {
        72: {'take_profit': 0.02, 'stop_loss': 0.01}, # v procentech
        144: {'take_profit': 0.03, 'stop_loss': 0.015}, # v procentech
        288: {'take_profit': 0.04, 'stop_loss': 0.02}, # v procentech
        720: {'take_profit': 0.05, 'stop_loss': 0.025}, # v procentech
    },
}

# Inicializace a připojení k IB
ib = IB()
try:
    ib.connect('127.0.0.1', 7497, clientId=1)
except ConnectionRefusedError:
    print(
        "Connection to Interactive Brokers refused. Please ensure TWS or IB Gateway is running and correctly configured.")
    exit()
except Exception as e:
    print(f"Connection error: {e}")
    exit()


def ascii():
    print(" ▄▄   ▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄▄ ▄▄▄▄▄▄  ▄▄▄ ▄▄   ▄▄ ")
    print(" █  █▄█  █       █       █      ██   █  █▄█  █ ")
    print(" █       █   ▄   █   ▄   █  ▄    █   █       █ ")
    print(" █       █  █ █  █  █ █  █ █ █   █   █       █ ")
    print(" █       █  █▄█  █  █▄█  █ █▄█   █   ██     █  ")
    print(" █ ██▄██ █       █       █       █   █   ▄   █ ")
    print(" █▄█   █▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄▄█▄▄▄▄▄▄██▄▄▄█▄▄█ █▄▄█ ")
    print("..................................... ver. O.3")
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


def calculate_trading_parameters():
    # Získání informací o účtu
    account_info = ib.accountSummary()
    account_size = None

    for item in account_info:
        if item.tag == 'TotalCashValue':
            print(f"Velikost účtu: {item.value} {item.currency}")
            account_size = float(item.value)
        elif item.tag == 'MaintMarginReq':
            print(f"Využitý margin: {item.value} {item.currency}")

    if account_size is not None:
        sorted_account_sizes = sorted(config['size_account'].keys(), reverse=True)

        # Najděte nejbližší nižší nebo rovnou hodnotu k velikosti účtu
        selected_account_size = None
        for size in sorted_account_sizes:
            if account_size >= size:
                selected_account_size = size
                break

        # Převod slovníku na DataFrame
        df = pd.json_normalize(config, sep='_')

        # Uložení config do CSV souboru
        df.to_csv('config.csv', index=False)

        if selected_account_size is not None:
            instrument_type = config['size_account'][selected_account_size]['type']
            print(f"Pro obchodování bude použit typ instrumentu: {instrument_type}")

            # Vypočítáme velikost účtu po páce
            leverage = config['leverage']
            leveraged_account_size = account_size * leverage
            config['leveraged_size_account'] = leveraged_account_size
            print(f"Velikost účtu po aplikaci páky: {leveraged_account_size:.2f} {item.currency}")

            # Získáme multiplikátor kontraktu
            long_contract = config['size_account'][selected_account_size]['long_contract']
            if instrument_type == 'SPY':
                contract_size = 400
            else:
                contract_size = float(long_contract.multiplier) * 4000

            # Vypočítáme, kolik kontraktů můžeme mít otevřeno najednou
            total_contracts = round(leveraged_account_size / contract_size)

            # Vypočítáme, kolik kontraktů můžeme mít na jeden obchod
            max_positions = config['max_positions']
            contracts_per_trade = round(total_contracts / max_positions)
            config['contracts_per_trade'] = contracts_per_trade
            print(
                f"Pro obchodování s {instrument_type} můžeme mít celkem otevřených {total_contracts:.2f} kontraktů na celý účet.")
            print(
                f"Pro obchodování s {instrument_type} můžeme mít otevřeno {contracts_per_trade:.2f} kontraktů na jeden obchod.")
            return selected_account_size
        else:
            print("Účet je příliš malý, nelze určit typ instrumentu.")
            return None
    else:
        print("Nepodařilo se získat informace o velikosti účtu.")
        return None


def contracts_spec():
    for account_size, details in config['size_account'].items():
        contract_type = details['type']
        if contract_type == 'SPY':
            spy_contract = Stock('SPY', 'SMART', 'USD')
            config['size_account'][account_size]['long_contract'] = spy_contract
        elif contract_type in ['MES', 'ES']:
            # Pro futures MES a ES najdeme nejbližší dostupný kontrakt
            contract = Future(contract_type, exchange='CME')
            contracts = ib.reqContractDetails(contract)
            print(contract)
            if contracts:
                nearest_contract = min(contracts, key=lambda x: x.contract.lastTradeDateOrContractMonth)
                config['size_account'][account_size]['long_contract'] = nearest_contract.contract
            else:
                print(f"Nenalezen žádný kontrakt pro {contract_type}")


def next_contracts_spec():
    for account_size, details in config['size_account'].items():
        contract_type = details['type']
        long_contract = details.get('long_contract')

        if contract_type == 'SPY':
            spy_contract = Stock('SPY', 'SMART', 'USD')
            config['size_account'][account_size]['short_contract'] = spy_contract
        elif contract_type in ['MES', 'ES']:
            contract = Future(contract_type, exchange='CME')
            contracts = ib.reqContractDetails(contract)

            if contracts:
                now = datetime.now()
                future_contracts = [c for c in contracts if
                                    datetime.strptime(c.contract.lastTradeDateOrContractMonth, "%Y%m%d") > now]

                if future_contracts:
                    # Odstraňte kontrakt, který je již nastaven jako long_contract
                    if long_contract:
                        future_contracts = [c for c in future_contracts if c.contract != long_contract]

                    if future_contracts:
                        next_contract = min(future_contracts, key=lambda x: x.contract.lastTradeDateOrContractMonth)
                        config['size_account'][account_size]['short_contract'] = next_contract.contract
                    else:
                        print(f"Žádný další budoucí kontrakt nenalezen pro {contract_type}")
                else:
                    print(f"Žádný budoucí kontrakt nenalezen pro {contract_type}")
            else:
                print(f"Nenalezen žádný kontrakt pro {contract_type}")


def display_grouped_orders(grouped_orders):
    print("------------------------------------------------------------------------")
    for parent_id, orders in grouped_orders.items():
        print(f"Obchodní skupina pro hlavní objednávku {parent_id}:")
        for trade in orders:
            contract = trade.contract
            order = trade.order
            order_status = trade.orderStatus
            print(
                f"{contract.symbol} > {contract.secType} {order.orderRef}> {order.action} > {order.orderType} > {order_status.status} > {order.totalQuantity} > {order.totalQuantity}")
        print()


def group_orders_by_parent(open_trades):
    grouped_orders = defaultdict(list)
    for trade in open_trades:
        parent_id = trade.order.parentId
        if parent_id == 0:
            parent_id = trade.order.orderId
        grouped_orders[parent_id].append(trade)
    return grouped_orders


def display_and_check_open_trades(config, open_trades):
    grouped_orders = group_orders_by_parent(open_trades)
    opened_mas = defaultdict(list)

    for parent_id, orders in grouped_orders.items():
        for trade in orders:
            contract = trade.contract
            order = trade.order
            order_status = trade.orderStatus

            # Získání klouzavého průměru z referencí objednávek
            ma = extract_moving_average_from_order_ref(order.orderRef)
            if ma is not None:
                opened_mas[ma].append(trade)

                # Zobrazení informací o obchodu
                # print(
                #     f"Hlavní objednávka (id {parent_id}) > Klouzavý průměr {ma} > Směr {order.action} > Status {order_status.status}")

    # Kontrola, zda pro každý klouzavý průměr již existuje otevřená objednávka
    mas_without_orders = []
    print("------------------------------------------------------------------------")
    for ma in config['ma_configurations']:
        if ma in opened_mas and any(trade.orderStatus.status in ['Submitted', 'Presubmitted'] for trade in opened_mas[ma]):
            print(f"Pro klouzavý průměr {ma} již existují otevřené obchody.")
        else:
            print(f"Pro klouzavý průměr {ma} neexistují žádné otevřené obchody.")
            mas_without_orders.append(ma)

    return mas_without_orders, opened_mas


def extract_moving_average_from_order_ref(order_ref):
    if order_ref is not None and isinstance(order_ref, str):
        ma_match = re.search(r'MA(\d+)', order_ref)
        if ma_match:
            return int(ma_match.group(1))
    return None


def get_moving_averages(instrument, duration, end_date):
    print("------------------------------------------------------------------------")
    print(f"Získávání klouzavých průměrů pro {instrument}...")
    contract = get_contract_for_instrument(instrument)

    print(f"Kontrakt pro získání klouzavých průměrů: {contract}")
    print(f"Délka historie: {duration}")
    print(f"Konečné datum a čas: {end_date}")
    print(f"Velikost svíčky: 10 mins")

    try:
        bars = ib.reqHistoricalData(
            contract,
            endDateTime=end_date,
            durationStr=duration,
            barSizeSetting='10 mins',
            whatToShow='TRADES',
            useRTH=False
        )
        if not bars:
            print("Nepodařilo se získat historická data.")
            return None

        df = util.df(bars)

        ma_values = {}
        for ma_period in config['ma_configurations'].keys():
            ma_column_name = f'MA{ma_period}'
            df[ma_column_name] = df['close'].rolling(window=ma_period).mean()
            ma_values[ma_period] = df[ma_column_name].iloc[-1]
            print(f"Klouzavý průměr {ma_period}: {ma_values[ma_period]}")

        return ma_values
    except Exception as e:
        print(f"Chyba při načítání historických dat: {e}")
        return None


def place_limit_order(action, instrument_type, ma_period, ma_value, ma_config, opened_mas):
    print("------------------------------------------------------------------------")
    if ma_period in opened_mas and opened_mas[ma_period]:
        print(f"Pro klouzavý průměr {ma_period} již existuje otevřená objednávka. Nová objednávka nebude umístěna.")
        return
    print(f"Vytváření {action} limitní objednávky pro {instrument_type} s klouzavým průměrem {ma_period}...")
    contract = get_contract_for_instrument(instrument_type)

    # Získejte aktuální cenu nástroje
    ticker = ib.reqMktData(contract)
    ib.sleep(1)  # Počkejte chvíli, aby se data aktualizoval
    current_price = ticker.marketPrice()
    print("Cena ", current_price, "MA ", ma_value)

    # Kontrola ceny vzhledem k akci a klouzavému průměru
    min_difference_percentage = config['min_difference']
    min_difference = ma_value * (min_difference_percentage / 100)
    if action == 'BUY' and (current_price - ma_value) < min_difference:
        print("Aktuální cena je příliš blízko nebo pod klouzavým průměrem, objednávka nebude odeslána.")
        return
    elif action == 'SELL' and (ma_value - current_price) < min_difference:
        print("Aktuální cena je příliš blízko nebo nad klouzavým průměrem, objednávka nebude odeslána.")
        return

    ma_value = round_to_quarter(ma_value)

    if action == 'BUY':
        stop_loss_price = round_to_quarter(ma_value * (1 - ma_config['stop_loss']))
        take_profit_price = round_to_quarter(ma_value * (1 + ma_config['take_profit']))
    else:  # SELL
        stop_loss_price = round_to_quarter(ma_value * (1 + ma_config['stop_loss']))
        take_profit_price = round_to_quarter(ma_value * (1 - ma_config['take_profit']))

    # Nastavte, jak dlouho má být objednávka platná (například 1 hodina)
    expiration_time = datetime.now() + timedelta(minutes=5)

    # Formátujte datum a čas pro IB API
    expiration_time_str = expiration_time.strftime("%Y%m%d %H:%M:%S")

    bracket_order = ib.bracketOrder(
        action=action,
        quantity=config['contracts_per_trade'],
        limitPrice=ma_value,
        takeProfitPrice=take_profit_price,
        stopLossPrice=stop_loss_price,
        outsideRth=True,
        orderRef=f"MA{ma_period}",
        tif='GTC'
    )

    # Nastavení GTD a expiračního času pouze pro hlavní objednávku
    bracket_order.parent.tif = 'GTD'
    bracket_order.parent.goodTillDate = expiration_time_str

    bracket_order.parent.orderRef = f"MA{ma_period}"

    main_trade = ib.placeOrder(contract, bracket_order.parent)
    ib.placeOrder(contract, bracket_order.takeProfit)
    ib.placeOrder(contract, bracket_order.stopLoss)

    for _ in range(10):
        ib.sleep(1)
        if main_trade.orderStatus.status in ['Submitted', 'Filled']:
            break

    if main_trade.orderStatus.status in ['Submitted', 'Filled']:
        print(f"Obchod {action} na {instrument_type} s klouzavým průměrem {ma_period} byl otevřen.")
        return main_trade
    else:
        print(f"Obchod {action} na {instrument_type} s klouzavým průměrem {ma_period} nebyl otevřen.")
        return None


def should_open_long(sentiment, trend):
    return (
            (sentiment == 'RiskOn' and trend in ['Growing', 'No trend', 'Sideways']) or
            (sentiment == 'RiskOff' and trend in ['Sideways', 'Fading'])
    )


def should_open_short(sentiment, trend):
    return sentiment == 'RiskOff' and trend == 'Growing'


def round_to_quarter(value):
    return round(value * 4) / 4


def get_contract_for_instrument(instrument):
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


# Hlavní smyčka
print("Spouštím hlavní smyčku...")
while True:
    try:
        # moodix sentiment
        sentiment, trend = get_market_sentiment(username, password)
        print("------------------------------------------------------------------------")
        print(f"Aktuální sentiment: {sentiment}, trend: {trend}")
        if sentiment is None:
            print("Nepodařilo se načíst sentiment. Čekám na další pokus.")
            time.sleep(60)
            continue
        print("------------------------------------------------------------------------")
        # nastaveni uct
        contracts_spec()
        next_contracts_spec()
        selected_account_size = calculate_trading_parameters()

        # Získání informací o otevřených obchodech
        open_trades = ib.openTrades()
        grouped_orders = group_orders_by_parent(open_trades)
        display_grouped_orders(grouped_orders)

        # Zobrazení a kontrola otevřených obchodů
        mas_without_orders, opened_mas = display_and_check_open_trades(config, open_trades)

        # Kontrola, zda byl vybrán typ účtu
        if selected_account_size is None:
            print("Chyba: Velikost účtu je příliš malá nebo se nepodařilo získat informace o účtu.")
            time.sleep(60)
            continue

        # Získání hodnot klouzavých průměrů
        instrument_type = config['size_account'][selected_account_size]['type']
        ma_values = get_moving_averages(instrument_type, '10 D', get_current_date_string())

        # Položení objednávek pro klouzavé průměry bez otevřených pozic
        for ma in mas_without_orders:
            # ma_value = ma_values[f'MA{ma}'].iloc[-1]
            ma_config = config['ma_configurations'][ma]
            ma_value = ma_values[ma]

            if should_open_long(sentiment, trend):
                # None
                place_limit_order('BUY', instrument_type, ma, ma_value, ma_config, opened_mas)
            elif should_open_short(sentiment, trend):
                # None
                place_limit_order('SELL', instrument_type, ma, ma_value, ma_config, opened_mas)

        # opened_mas = []
        # mas_without_orders = []
        # Počkejte 5 sekund před dalším během smyčky
        print("Čekám 5 sekund před dalším cyklem...")
        time.sleep(5)
    except Exception as e:
        print(f"Chyba při komunikaci s brokerem na API: {e}")
        time.sleep(60)
