import pandas as pd

# Конфигурационные параметры
import config

# Получаем данные из таблицы
df = pd.read_excel(config.file_path)

# Инициализация начального баланса
balance = config.initial_balance
total_unclosed_amount = 0  # Для подсчета всех оставшихся средств

# Статистика
trades_total = 0
trades_with_profit = 0
trades_with_loss = 0
tp_hit_count = [0] * len(config.take_profit_percentages)
profit_loss_ratio = 0
initial_balance = config.initial_balance

# Функция для обработки одной сделки
def process_trade(entry_price, deep_price, ath_price, token, index):
    global balance
    global total_unclosed_amount

    # Рассчитываем Stop Loss
    stop_loss_price = entry_price * (1 + config.stop_loss_percent / 100)

    # Рассчитываем все уровни TP
    tp_prices = [entry_price * (1 + tp / 100) for tp in config.take_profit_percentages]

    position_percentage = config.position_percentages
    remaining_position = config.deal_amount

    # Начинаем сделку
    print(f"→ Starting trade {index + 1} - Token: 🪙 {token}")
    print(f"Entry Price: 💰 {entry_price:.10f}, Stop Loss: ⬇️🛑 {stop_loss_price:.10f}")
    print(f"Take Profits: {', '.join([f'↗️🟢 {tp:.10f}' for tp in tp_prices])}")

    # Покупаем токены, уменьшая баланс на сумму сделки
    balance -= remaining_position

    # Проверка стоп-лосса
    stop_loss_hit = deep_price <= stop_loss_price
    if stop_loss_hit:
        # Если сработал стоп-лосс, закрываем позицию и списываем сумму убытка
        loss = remaining_position * abs(config.stop_loss_percent) / 100
        balance -= loss
        remaining_position = 0
        print(f"⬇️❌ Stop Loss hit at price {deep_price:.10f}, position closed, loss: {loss:.2f}$")
        print(f"🤔 Remaining unclosed position: {remaining_position:.2f}$")
        print(f"Final Balance after trade {index + 1}: 🙉 {balance:.2f}$, excluding unclosed position")
        print(f"😬 Unclosed Amount (remaining in position): {remaining_position:.2f}$")
        print("-" * 50)
        return remaining_position

    # Обрабатываем уровни Take Profit
    remaining_position_after_tps = remaining_position  # Остаток позиции
    total_profit = 0  # Общая прибыль от TP

    for i, tp in enumerate(tp_prices):
        if ath_price >= tp:  # Если максимальная цена после входа превышает TP
            # Рассчитываем фиксированную сумму на текущем уровне TP
            fixed_position = remaining_position_after_tps * position_percentage[i] / 100
            remaining_position_after_tps -= fixed_position

            # Прибыль с этой позиции
            profit = fixed_position * (tp - entry_price) / entry_price
            total_profit += fixed_position + profit  # Добавляем фиксированную сумму и прибыль

            print(f"⬆️ TP {tp:.10f} hit, position closed {position_percentage[i]:.2f}% (💵 Profit: {fixed_position + profit:.2f}$)")

    # Выводим информацию по сделке
    if total_profit > 0:
        print(f"🎯 Result: Successful TP hit")
    else:
        print(f"💩 Result: No TP hit")

    print(f"🤔 Remaining unclosed position: {remaining_position_after_tps:.2f}$")
    balance += total_profit  # Добавляем прибыль к балансу
    print(f"Final Balance after trade {index + 1}: 💅 {balance:.2f}$, excluding unclosed position")
    print(f"😬 Unclosed Amount (remaining in position): {remaining_position_after_tps:.2f}$")
    print("-" * 50)

    # Добавляем к общей сумме оставшихся средств
    total_unclosed_amount += remaining_position_after_tps

    # Возвращаем оставшуюся позицию для следующей сделки
    return remaining_position_after_tps

print("\n--- Configuration Parameters ---")
print(f"Initial Balance: {config.initial_balance}")
print(f"Deal Amount per Trade: {config.deal_amount}")
print(f"Stop Loss Percentage: {config.stop_loss_percent}%")
print(f"Take Profit Percentages: {config.take_profit_percentages}")
print(f"Position Percentages: {config.position_percentages}")
print(f"Max Take Profit Levels: {config.max_take_profit_levels}")
print("--- End of Configuration ---\n")

# Основной цикл обработки сделок
for i, row in df.iterrows():
    # Получаем данные из таблицы
    entry_price = row['EntryPrice']
    deep_price = row['DeepPrice']
    ath_price = row['ATHpriceAfterSignal']

    # Обрабатываем сделку
    trades_total += 1
    remaining_position = process_trade(entry_price, deep_price, ath_price, row['Token'], i)

    # Подсчет статистики по сделкам
    if deep_price <= entry_price * (1 + config.stop_loss_percent / 100):
        trades_with_loss += 1
    elif ath_price >= min([entry_price * (1 + tp / 100) for tp in config.take_profit_percentages]):
        trades_with_profit += 1
        for j, tp in enumerate([entry_price * (1 + tp / 100) for tp in config.take_profit_percentages]):
            if ath_price >= tp:
                tp_hit_count[j] += 1

# Финальный вывод статистики
if trades_with_loss > 0:
    profit_loss_ratio = trades_with_profit / trades_with_loss
else:
    profit_loss_ratio = trades_with_profit

x_return = (balance - initial_balance) / initial_balance

print(f"\n--- ✨ Final Statistics ✨ ---")
print(f"Total Trades Processed: {trades_total} ⚡️")
print(f"Trades Closed with Profit: {trades_with_profit} 🦡")
print(f"Trades Closed with Loss (SL hit): {trades_with_loss}❌")
for k, tp_count in enumerate(tp_hit_count):
    print(f"Trades Closed at TP Level {k + 1}: {tp_count} ✅")
print(f"Profit/Loss Ratio: {profit_loss_ratio:.2f} 🤖")
print(f"Total X Return on Balance: {x_return:.2f}x 🌚")
print("--- ✨ End of Statistics ✨ ---\n")

# Финальный вывод баланса и оставшихся средств
print(f"\nFinal Balance after all trades: 💅 {balance:.2f}$")
print(f"💀 Total Unclosed Amount across all trades: {total_unclosed_amount:.2f}$")
