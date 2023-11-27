def close_order(ib, order_id):
    """
    Funkce pro uzavření objednávky s daným ID.
    """
    try:
        ib.cancelOrder(order_id)
        print(f"Objednávka {order_id} byla zrušena.")
    except Exception as e:
        print(f"Nepodařilo se zrušit objednávku {order_id}: {e}")


def is_bracket_order(order, ma_identifiers):
    """
    Funkce pro ověření, zda objednávka je součástí 'bracket' objednávek.
    """
    return any(str(ma_id) in order.orderRef for ma_id in ma_identifiers)


def get_unfilled_bracket_orders(ib, ma_identifiers):
    """
    Funkce získá seznam nevyplněných limitních 'bracket' objednávek.
    """
    open_orders = ib.reqOpenOrders()
    unfilled_bracket_orders = []

    for order in open_orders:
        if order.orderType == 'LMT' and order.orderState.status != 'Filled' and is_bracket_order(order, ma_identifiers):
            unfilled_bracket_orders.append(order)

    return unfilled_bracket_orders


def close_unfilled_bracket_orders(ib, ma_identifiers):
    """
    Funkce uzavře všechny nevyplněné limitní 'bracket' objednávky.
    """
    unfilled_bracket_orders = get_unfilled_bracket_orders(ib, ma_identifiers)
    for order in unfilled_bracket_orders:
        close_order(ib, order.orderId)
