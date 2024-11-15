# optimizer.py
import config
import main  # импортируем основной файл для обработки сделок
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from sklearn.model_selection import RandomizedSearchCV
import threading
import time

# Определяем диапазоны параметров для поиска наилучшего значения баланса
DEAL_AMOUNT_BOUNDS = (10, 100)  # диапазон для суммы на сделку
STOP_LOSS_PERCENT_BOUNDS = (-50, -50)  # фиксированный стоп-лосс
TAKE_PROFIT_PERCENTAGES_BOUNDS = [(100, 700), (150, 750), (200, 800)]  # диапазоны для уровней TP
POSITION_PERCENTAGES_BOUNDS = [(10, 100), (10, 100), (100, 100)]  # диапазон для закрытия позиции на каждом уровне TP
MACHINE_MODE = True  # Если True, то меняет параметры TAKE_PROFIT_PERCENTAGES_BOUNDS и POSITION_PERCENTAGES_BOUNDS на свое усмотрение
MAX_TIME_MINUTES = 3  # Максимальное время работы модуля в минутах

# Чтение данных из файла
input_data = pd.read_excel(config.file_path)

# Функция для запуска основной программы с текущими параметрами и возврата итогового баланса
def run_simulation(deal_amount, stop_loss_percent, take_profit_percentages, position_percentages):
    # Устанавливаем параметры в config.py
    config.deal_amount = deal_amount
    config.stop_loss_percent = stop_loss_percent
    config.take_profit_percentages = take_profit_percentages
    config.position_percentages = position_percentages

    # Сбрасываем начальные значения
    main.balance = config.initial_balance
    main.total_unclosed_amount = 0
    main.trades_total = 0
    main.trades_with_profit = 0
    main.trades_with_loss = 0
    main.tp_hit_count = [0] * len(config.take_profit_percentages)
    main.profit_loss_ratio = 0

    # Запускаем основной цикл обработки сделок
    for i, row in input_data.iterrows():
        main.process_trade(row['EntryPrice'], row['DeepPrice'], row['ATHpriceAfterSignal'], row['Token'], i)

    # Возвращаем итоговый баланс
    return main.balance

# Целевая функция для оптимизации
def objective_function(params):
    deal_amount = params[0]
    stop_loss_percent = -50  # Фиксированный стоп-лосс
    take_profit_percentages = params[1:4]
    position_percentages = params[4:7]

    # Запускаем симуляцию и возвращаем отрицательное значение баланса (так как оптимизируем минимум)
    final_balance = run_simulation(deal_amount, stop_loss_percent, take_profit_percentages, position_percentages)
    return -final_balance

# Основная функция для подбора наилучших параметров с использованием дифференциальной эволюции
def differential_evolution_optimization(result_dict):
    bounds = [
        DEAL_AMOUNT_BOUNDS,
        TAKE_PROFIT_PERCENTAGES_BOUNDS[0],
        TAKE_PROFIT_PERCENTAGES_BOUNDS[1],
        TAKE_PROFIT_PERCENTAGES_BOUNDS[2],
        POSITION_PERCENTAGES_BOUNDS[0],
        POSITION_PERCENTAGES_BOUNDS[1],
        POSITION_PERCENTAGES_BOUNDS[2]
    ]

    start_time = time.time()
    result = differential_evolution(
        objective_function,
        bounds,
        strategy='best1bin',
        maxiter=50,
        popsize=10,
        tol=0.01,
        callback=lambda x, convergence: time.time() - start_time > MAX_TIME_MINUTES * 60
    )

    # Извлекаем наилучшие параметры
    best_params = result.x
    best_balance = -result.fun

    # Сохраняем результаты в словарь
    result_dict['Differential Evolution'] = (best_balance, best_params)

    # Выводим наилучшие параметры и итоговый баланс
    print("\n--- Differential Evolution Best Parameters Found ---")
    print(f"Deal Amount: {best_params[0]:.2f}")
    print(f"Stop Loss Percent: -50.00 (фиксированный)")
    print(f"Take Profit Percentages: [{best_params[1]:.2f}, {best_params[2]:.2f}, {best_params[3]:.2f}]")
    print(f"Position Percentages: [{best_params[4]:.2f}, {best_params[5]:.2f}, {best_params[6]:.2f}]")
    print(f"Best Final Balance: {best_balance:.2f}$")

# Функция для оптимизации параметров с использованием случайного поиска
def randomized_search_optimization(result_dict):
    # Определение параметров для случайного поиска
    param_distributions = {
        'deal_amount': np.linspace(DEAL_AMOUNT_BOUNDS[0], DEAL_AMOUNT_BOUNDS[1], num=10),
        'take_profit_percentages': [
            (np.random.uniform(100, 700), np.random.uniform(150, 750), np.random.uniform(200, 800))
        ],
        'position_percentages': [
            (np.random.uniform(10, 100), np.random.uniform(10, 100), 100)
        ]
    }

    start_time = time.time()
    best_params = None
    best_balance = -float('inf')

    while time.time() - start_time < MAX_TIME_MINUTES * 60:
        deal_amount = np.random.choice(param_distributions['deal_amount'])
        take_profit_percentages = param_distributions['take_profit_percentages'][0]
        position_percentages = param_distributions['position_percentages'][0]

        # Запускаем симуляцию
        final_balance = run_simulation(deal_amount, -50, take_profit_percentages, position_percentages)

        # Сравниваем баланс
        if final_balance > best_balance:
            best_balance = final_balance
            best_params = (deal_amount, take_profit_percentages, position_percentages)

    # Сохраняем результаты в словарь
    result_dict['Randomized Search'] = (best_balance, best_params)

    # Выводим наилучшие параметры и итоговый баланс
    print("\n--- Randomized Search Best Parameters Found ---")
    print(f"Deal Amount: {best_params[0]:.2f}")
    print(f"Stop Loss Percent: -50.00 (фиксированный)")
    print(f"Take Profit Percentages: {best_params[1]}")
    print(f"Position Percentages: {best_params[2]}")
    print(f"Best Final Balance: {best_balance:.2f}$")

# Функция для оптимизации с использованием градиентного спуска (имитация)
def gradient_descent_optimization(result_dict):
    # Параметры начальной точки
    deal_amount = np.mean(DEAL_AMOUNT_BOUNDS)
    take_profit_percentages = [300, 400, 500]
    position_percentages = [50, 75, 100]
    learning_rate = 1
    best_balance = run_simulation(deal_amount, -50, take_profit_percentages, position_percentages)
    best_params = (deal_amount, take_profit_percentages, position_percentages)

    start_time = time.time()
    while time.time() - start_time < MAX_TIME_MINUTES * 60:
        # Немного изменяем параметры в зависимости от градиента
        deal_amount += np.random.uniform(-learning_rate, learning_rate)
        take_profit_percentages = [tp + np.random.uniform(-learning_rate, learning_rate) for tp in take_profit_percentages]
        position_percentages = [pp + np.random.uniform(-learning_rate, learning_rate) for pp in position_percentages]

        # Запускаем симуляцию
        final_balance = run_simulation(deal_amount, -50, take_profit_percentages, position_percentages)

        # Сравниваем баланс
        if final_balance > best_balance:
            best_balance = final_balance
            best_params = (deal_amount, take_profit_percentages, position_percentages)

    # Сохраняем результаты в словарь
    result_dict['Gradient Descent'] = (best_balance, best_params)

    # Выводим наилучшие параметры и итоговый баланс
    print("\n--- Gradient Descent Best Parameters Found ---")
    print(f"Deal Amount: {best_params[0]:.2f}")
    print(f"Stop Loss Percent: -50.00 (фиксированный)")
    print(f"Take Profit Percentages: {best_params[1]}")
    print(f"Position Percentages: {best_params[2]}")
    print(f"Best Final Balance: {best_balance:.2f}$")

# Запуск оптимизации в параллельных потоках
if __name__ == "__main__":
    # Словарь для хранения результатов
    result_dict = {}

    # Создаем три потока для выполнения разных алгоритмов оптимизации
    thread1 = threading.Thread(target=differential_evolution_optimization, args=(result_dict,))
    thread2 = threading.Thread(target=randomized_search_optimization, args=(result_dict,))
    thread3 = threading.Thread(target=gradient_descent_optimization, args=(result_dict,))

    # Запускаем потоки
    thread1.start()
    thread2.start()
    thread3.start()

    # Ожидаем завершения потоков
    thread1.join()
    thread2.join()
    thread3.join()

    # Выводим результаты всех алгоритмов
    print("\n--- Summary of Best Results from All Algorithms ---")
    for algo, (balance, params) in result_dict.items():
        print(f"{algo}: Best Final Balance = {balance:.2f}$")
        print(f"Parameters: {params}")
