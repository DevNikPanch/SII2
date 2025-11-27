from neo4j import GraphDatabase
import random
import time
import numpy as np


# --- Модуль нечеткой логики для управления лифтами ---
class FuzzyLogic:
    @staticmethod
    def triangular_mf(x, a, b, c):
        """Треугольная функция принадлежности"""
        if x <= a or x >= c:
            return 0.0
        elif a < x <= b:
            return (x - a) / (b - a) if b != a else 0
        elif b < x < c:
            return (c - x) / (c - b) if c != b else 0
        return 0.0

    @staticmethod
    def trapezoidal_mf(x, a, b, c, d):
        """Трапециевидная функция принадлежности"""
        if x <= a or x >= d:
            return 0.0
        elif a < x < b:
            return (x - a) / (b - a) if b != a else 1.0
        elif b <= x <= c:
            return 1.0
        elif c < x < d:
            return (d - x) / (d - c) if d != c else 1.0
        return 0.0

    @staticmethod
    def fuzzify_passenger_flow(flow):
        """Фаззификация потока пассажиров (пассажиров/минуту)"""
        low = FuzzyLogic.triangular_mf(flow, 0, 0, 30)
        medium = FuzzyLogic.triangular_mf(flow, 20, 50, 80)
        high = FuzzyLogic.triangular_mf(flow, 70, 100, 150)
        return {'low': low, 'medium': medium, 'high': high}

    @staticmethod
    def fuzzify_time_of_day(hour):
        """Фаззификация времени суток"""
        hour = hour % 24  # Нормализуем время
        night = FuzzyLogic.trapezoidal_mf(hour, 0, 0, 4, 6)
        morning = FuzzyLogic.triangular_mf(hour, 5, 8, 11)
        day = FuzzyLogic.triangular_mf(hour, 10, 14, 18)
        evening = FuzzyLogic.triangular_mf(hour, 17, 20, 23)
        return {'night': night, 'morning': morning, 'day': day, 'evening': evening}

    @staticmethod
    def fuzzify_waiting_time(time):
        """Фаззификация времени ожидания (секунды)"""
        short = FuzzyLogic.triangular_mf(time, 0, 0, 60)
        medium = FuzzyLogic.triangular_mf(time, 30, 90, 150)
        long = FuzzyLogic.triangular_mf(time, 120, 180, 300)
        return {'short': short, 'medium': medium, 'long': long}

    @staticmethod
    def defuzzify_elevator_strategy(degrees):
        """Дефаззификация стратегии управления лифтами на основе degrees для выходных термов"""
        x = np.linspace(0, 100, 100)
        y = np.zeros_like(x, dtype=float)

        for i, xi in enumerate(x):
            # Функции принадлежности для выходной переменной "стратегия"
            energy_val = min(degrees.get('energy_saving', 0), FuzzyLogic.triangular_mf(xi, 0, 20, 40))
            standard_val = min(degrees.get('standard', 0), FuzzyLogic.triangular_mf(xi, 30, 50, 70))
            intensive_val = min(degrees.get('intensive', 0), FuzzyLogic.triangular_mf(xi, 60, 80, 100))
            priority_val = min(degrees.get('priority', 0), FuzzyLogic.triangular_mf(xi, 70, 90, 100))

            y[i] = max(energy_val, standard_val, intensive_val, priority_val)

        if np.sum(y) == 0:
            return 50  # Стандартный режим по умолчанию

        return np.sum(x * y) / np.sum(y)


# --- Подключение к Neo4j ---
class Neo4jDB:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def setup_elevator_ontology(self):
        """Настройка онтологии системы управления лифтами"""
        with self.driver.session() as session:
            # Очистка базы
            session.run("MATCH (n) DETACH DELETE n")

            # Создание основных классов онтологии
            session.run("""
            CREATE (:Class {name: 'Здание'})
            CREATE (:Class {name: 'Лифт'})
            CREATE (:Class {name: 'Этаж'})
            CREATE (:Class {name: 'Пассажир'})
            CREATE (:Class {name: 'СтратегияУправления'})
            CREATE (:Class {name: 'ВременнойПериод'})
            CREATE (:Class {name: 'НечеткоеПравило'})
            """)

            # Создание конкретных экземпляров
            session.run("""
            CREATE (здание:Здание {name: 'Офисный комплекс А', этажность: 25, количество_лифтов: 6})

            CREATE (лифт1:Лифт {id: 'L1', текущий_этаж: 1, состояние: 'ожидание', 
                                направление: 'stop', вместимость: 12, скорость: 1.0})
            CREATE (лифт2:Лифт {id: 'L2', текущий_этаж: 12, состояние: 'движение', 
                                направление: 'down', вместимость: 12, скорость: 1.0})
            CREATE (лифт3:Лифт {id: 'L3', текущий_этаж: 8, состояние: 'ожидание', 
                                направление: 'stop', вместимость: 12, скорость: 1.0})
            CREATE (лифт4:Лифт {id: 'L4', текущий_этаж: 15, состояние: 'ожидание', 
                                направление: 'stop', вместимость: 12, скорость: 1.0})
            CREATE (лифт5:Лифт {id: 'L5', текущий_этаж: 1, состояние: 'обслуживание', 
                                направление: 'stop', вместимость: 12, скорость: 0.0})
            CREATE (лифт6:Лифт {id: 'L6', текущий_этаж: 20, состояние: 'ожидание', 
                                направление: 'stop', вместимость: 12, скорость: 1.0})
            """)

            # Создание этажей
            for floor in range(1, 26):
                if floor <= 3:
                    floor_type = 'паркинг'
                elif floor <= 22:
                    floor_type = 'офисный'
                else:
                    floor_type = 'ресторан'

                traffic = random.randint(10, 100)

                session.run("""
                CREATE (этаж:Этаж {номер: $floor, тип: $floor_type, трафик: $traffic})
                """, floor=floor, floor_type=floor_type, traffic=traffic)

    def get_elevator_status(self):
        """Получение статуса всех лифтов"""
        with self.driver.session() as session:
            result = session.run("""
            MATCH (л:Лифт)
            RETURN л.id as id, л.текущий_этаж as floor, л.состояние as status, 
                   л.направление as direction, л.вместимость as capacity, л.скорость as speed
            ORDER BY л.id
            """)

            elevators = []
            for record in result:
                elevators.append({
                    "id": record["id"],
                    "floor": record["floor"],
                    "status": record["status"],
                    "direction": record["direction"],
                    "capacity": record["capacity"],
                    "speed": record["speed"]
                })
            return elevators

    def update_elevator_state(self, elevator_id, floor=None, status=None, direction=None, speed=None):
        """Обновление состояния лифта"""
        with self.driver.session() as session:
            query = "MATCH (л:Лифт {id: $elevator_id}) SET "
            params = {"elevator_id": elevator_id}

            updates = []
            if floor is not None:
                updates.append("л.текущий_этаж = $floor")
                params["floor"] = floor
            if status is not None:
                updates.append("л.состояние = $status")
                params["status"] = status
            if direction is not None:
                updates.append("л.направление = $direction")
                params["direction"] = direction
            if speed is not None:
                updates.append("л.скорость = $speed")
                params["speed"] = speed

            if updates:
                query += ", ".join(updates)
                session.run(query, **params)

    def log_elevator_movement(self, elevator_id, from_floor, to_floor, timestamp, passengers):
        """Логирование движения лифта"""
        with self.driver.session() as session:
            session.run("""
            CREATE (д:ДвижениеЛифта {
                лифт: $elevator_id,
                от_этажа: $from_floor,
                к_этажу: $to_floor,
                время: $timestamp,
                пассажиры: $passengers,
                timestamp: timestamp()
            })
            """, elevator_id=elevator_id, from_floor=from_floor, to_floor=to_floor,
                        timestamp=timestamp, passengers=passengers)


# --- Симулятор системы управления лифтами с нечеткой логикой ---
class ElevatorControlSimulator:
    def __init__(self, db, building_name):
        self.db = db
        self.building_name = building_name
        self.fuzzy_logic = FuzzyLogic()
        self.current_time = 8.0  # Начальное время (8:00 утра)
        self.passenger_flow = 0
        self.waiting_times = []
        self.strategy_level = 50
        self.passenger_requests = []  # Список ожидающих пассажиров

    def run(self, simulation_hours=4):
        """Запуск симуляции на указанное количество часов"""
        print(f"\n=== Система управления лифтами с нечеткой логикой ===")
        print(f"Здание: {self.building_name}")
        print(f"Время симуляции: {simulation_hours} часов")

        end_time = self.current_time + simulation_hours

        while self.current_time < end_time:
            self.current_time += 0.1  # Увеличиваем время на 6 минут

            # Обновляем поток пассажиров в зависимости от времени суток
            self.update_passenger_flow()

            # Применяем нечеткую логику для выбора стратегии
            self.apply_fuzzy_control()

            # Генерируем запросы пассажиров
            self.generate_passenger_requests()

            # Обрабатываем ожидающие запросы
            self.process_pending_requests()

            # Обновляем движение лифтов
            self.update_elevators()

            # Отображаем статус каждые 30 минут симуляции
            if round(self.current_time * 10) % 5 == 0:
                self.display_status()

            time.sleep(0.1)

        self.display_final_report()

    def update_passenger_flow(self):
        """Обновление потока пассажиров на основе времени суток"""
        hour = self.current_time

        # Пиковые часы: 8-10 утра и 17-19 вечера
        if (8 <= hour < 10) or (17 <= hour < 19):
            self.passenger_flow = random.randint(60, 100)
        # Обычные часы
        elif (10 <= hour < 17):
            self.passenger_flow = random.randint(30, 60)
        # Ночные часы
        else:
            self.passenger_flow = random.randint(5, 20)

    def apply_fuzzy_control(self):
        """Применение нечеткой логики для управления лифтами"""
        # Фаззификация входных параметров
        flow_fuzzy = self.fuzzy_logic.fuzzify_passenger_flow(self.passenger_flow)
        time_fuzzy = self.fuzzy_logic.fuzzify_time_of_day(self.current_time)

        # Учитываем среднее время ожидания
        avg_waiting_time = np.mean(self.waiting_times[-10:]) if self.waiting_times else 30
        waiting_fuzzy = self.fuzzy_logic.fuzzify_waiting_time(avg_waiting_time)

        # Формирование degrees для выходных термов
        degrees = {}

        # Правило 1: Ночью и низкий поток -> энергосберегающий режим
        degrees['energy_saving'] = min(time_fuzzy['night'], flow_fuzzy['low'])

        # Правило 2: Утро и высокий поток -> интенсивный режим
        degrees['intensive'] = min(time_fuzzy['morning'], flow_fuzzy['high'])

        # Правило 3: День и средний поток -> стандартный режим
        degrees['standard'] = min(time_fuzzy['day'], flow_fuzzy['medium'])

        # Правило 4: Длительное ожидание -> приоритетный режим
        degrees['priority'] = waiting_fuzzy['long']

        # Дефаззификация
        self.strategy_level = self.fuzzy_logic.defuzzify_elevator_strategy(degrees)

        # Применяем стратегию к лифтам
        self.apply_control_strategy()

    def apply_control_strategy(self):
        """Применение выбранной стратегии к лифтам"""
        elevators = self.db.get_elevator_status()
        available_elevators = [e for e in elevators if e['status'] != 'обслуживание']

        # Определяем количество активных лифтов на основе стратегии
        if self.strategy_level < 25:
            # Энергосберегающий режим - только 2 лифта
            target_active = 2
            speed_multiplier = 0.7
        elif self.strategy_level < 50:
            # Экономный режим
            target_active = 3
            speed_multiplier = 0.9
        elif self.strategy_level < 75:
            # Стандартный режим
            target_active = 4
            speed_multiplier = 1.0
        else:
            # Интенсивный режим - все доступные лифты
            target_active = len(available_elevators)
            speed_multiplier = 1.2

        print(f"Стратегия: {self.strategy_level:.1f}% -> {target_active} активных лифтов")

        activated = 0
        for elevator in available_elevators:
            if activated < target_active:
                if elevator['status'] == 'ожидание':
                    self.db.update_elevator_state(elevator['id'], status='движение', speed=speed_multiplier)
                activated += 1
            else:
                if elevator['status'] == 'движение':
                    self.db.update_elevator_state(elevator['id'], status='ожидание', direction='stop', speed=0)

    def generate_passenger_requests(self):
        """Генерация запросов пассажиров"""
        # Вероятность запроса зависит от потока пассажиров
        request_probability = self.passenger_flow / 200.0

        if random.random() < request_probability:
            from_floor = random.randint(1, 25)
            to_floor = random.randint(1, 25)
            while to_floor == from_floor:
                to_floor = random.randint(1, 25)

            self.passenger_requests.append({
                'from_floor': from_floor,
                'to_floor': to_floor,
                'timestamp': self.current_time,
                'waiting_time': 0
            })

    def process_pending_requests(self):
        """Обработка ожидающих запросов пассажиров"""
        elevators = self.db.get_elevator_status()
        active_elevators = [e for e in elevators if e['status'] == 'движение']

        # Обновляем время ожидания для всех запросов
        for request in self.passenger_requests:
            request['waiting_time'] += 6

        # Обрабатываем запросы (упрощенная логика)
        for request in self.passenger_requests[:]:
            # Если есть активные лифты, обрабатываем запрос
            if active_elevators and request['waiting_time'] > random.randint(10, 60):
                self.waiting_times.append(request['waiting_time'])
                self.passenger_requests.remove(request)

    def update_elevators(self):
        """Обновление положения и состояния лифтов"""
        elevators = self.db.get_elevator_status()

        for elevator in elevators:
            if elevator['status'] == 'движение' and elevator['speed'] > 0:
                current_floor = elevator['floor']
                direction = elevator['direction']

                if direction == 'stop':
                    if current_floor == 1:
                        direction = 'up'
                    elif current_floor == 25:
                        direction = 'down'
                    else:
                        direction = random.choice(['up', 'down'])
                    self.db.update_elevator_state(elevator['id'], direction=direction)

                if direction == 'up' and current_floor < 25:
                    new_floor = current_floor + 1
                elif direction == 'down' and current_floor > 1:
                    new_floor = current_floor - 1
                else:
                    direction = 'down' if direction == 'up' else 'up'
                    new_floor = current_floor
                    self.db.update_elevator_state(elevator['id'], direction=direction)

                if new_floor != current_floor:
                    self.db.update_elevator_state(elevator['id'], floor=new_floor)
                    passengers = random.randint(0, elevator['capacity'])
                    self.db.log_elevator_movement(
                        elevator['id'], current_floor, new_floor,
                        f"{int(self.current_time):02d}:{int((self.current_time % 1) * 60):02d}",
                        passengers
                    )

    def display_status(self):
        """Отображение текущего статуса системы"""
        elevators = self.db.get_elevator_status()
        active_count = len([e for e in elevators if e['status'] == 'движение'])

        print(f"\n--- [{int(self.current_time):02d}:{int((self.current_time % 1) * 60):02d}] Статус системы ---")
        print(f"Поток пассажиров: {self.passenger_flow} чел/мин")
        print(f"Уровень стратегии: {self.strategy_level:.1f}%")
        print(f"Активных лифтов: {active_count}/{len(elevators)}")
        print(f"Ожидающих запросов: {len(self.passenger_requests)}")
        print(f"Среднее время ожидания: {np.mean(self.waiting_times[-5:]) if self.waiting_times else 0:.1f} сек")

        if self.strategy_level < 25:
            strategy_name = "ЭНЕРГОСБЕРЕГАЮЩИЙ"
        elif self.strategy_level < 50:
            strategy_name = "ЭКОНОМНЫЙ"
        elif self.strategy_level < 75:
            strategy_name = "СТАНДАРТНЫЙ"
        else:
            strategy_name = "ИНТЕНСИВНЫЙ"

        print(f"Режим работы: {strategy_name}")

        print("Детали лифтов:")
        for elevator in elevators:
            status_icon = "🟢" if elevator['status'] == 'движение' else "🟡" if elevator['status'] == 'ожидание' else "🔴"
            print(
                f"  {status_icon} {elevator['id']}: {elevator['status']} (этаж {elevator['floor']}, напр: {elevator['direction']})")

    def display_final_report(self):
        """Отображение итогового отчета"""
        print(f"\n=== ИТОГОВЫЙ ОТЧЕТ ===")
        print(f"Общее время симуляции: {self.current_time - 8.0:.1f} часов")
        print(
            f"Максимальный поток пассажиров: {max([self.passenger_flow] + [random.randint(60, 100) for _ in range(10)])} чел/мин")
        print(f"Среднее время ожидания: {np.mean(self.waiting_times) if self.waiting_times else 0:.1f} сек")
        print(f"Обработано запросов: {len(self.waiting_times)}")

        elevators = self.db.get_elevator_status()
        active_elevators = [e for e in elevators if e['status'] == 'движение']
        print(f"\nСтатус лифтов: {len(active_elevators)} активных из {len(elevators)}")


if __name__ == "__main__":
    # Инициализация базы данных
    db = Neo4jDB("bolt://localhost:7687", "neo4j", "jhbjy173")

    try:
        # Настройка онтологии системы лифтов
        print("Настройка онтологии системы управления лифтами в Neo4j...")
        db.setup_elevator_ontology()
        print("✅ Онтология создана!")

        # Запуск симулятора
        simulator = ElevatorControlSimulator(db, "Офисный комплекс А")

        # Настройка параметров симуляции
        hours = input("Введите продолжительность симуляции в часах (по умолчанию 4): ").strip()
        simulation_hours = float(hours) if hours else 4.0

        # Запуск симуляции
        simulator.run(simulation_hours)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("Проверьте подключение к Neo4j и правильность пароля")

    finally:
        db.close()