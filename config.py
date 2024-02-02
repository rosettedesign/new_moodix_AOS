config = {
    'size_account': {
        500: {'type': 'SPY'},
        20000: {'type': 'MES'},
        200000: {'type': 'ES'}
    },
    'leverage': 4,
    'long_trades': True,
    'short_trades': False,
    'max_positions': 4,
    'max_ma': 720,  # pro ES/MES nastavit 720
    'min_difference': 0.01,  # v procentech
    'ma_configurations': {
        # nastavení pro SPY nebo-li CFD IBUS500, pro ES/MES je nastavení MA 72 - 144 - 288 - 720
        72: {'take_profit': 0.007, 'stop_loss': 0.005, 'next': 144, 'distance': 4},  # v procentech
        144: {'take_profit': 0.011, 'stop_loss': 0.007, 'next': 288, 'distance': 6},  # v procentech
        288: {'take_profit': 0.015, 'stop_loss': 0.011, 'next': 720, 'distance': 8},  # v procentech
        720: {'take_profit': 0.019, 'stop_loss': 0.015, 'next': 720, 'distance': 10},  # v procentech
    },
}
