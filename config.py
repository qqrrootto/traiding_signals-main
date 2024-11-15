# config.py

# Основные параметры конфигурации

initial_balance = 1000  # Начальный баланс
deal_amount = 100       # Сумма на сделку
stop_loss_percent = -50  # Процент стоп-лосса
take_profit_percentages = [100, 200, 300]  # Проценты для каждого уровня TP
position_percentages = [50, 50, 50]  # Процент закрытия позиции на каждом уровне TP

file_path = 'input.xlsx'  # Путь к файлу с данными (вместо жестко прописанного пути)

# Дополнительные настройки (например, количество уровней TP)
max_take_profit_levels = 3
