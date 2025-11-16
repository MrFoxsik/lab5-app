# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
from dataclasses import dataclass

# ---------- DOMAIN (доменная модель) ----------

@dataclass
class AbstractCar:
    brand: str
    model: str
    base_price: float
    curb_weight: float


@dataclass
class ICECar(AbstractCar):
    engine_capacity: float = 0.0
    fuel_type: str = ""
    emission_class: str = ""


@dataclass
class ElectricCar(AbstractCar):
    max_range_km: int = 0
    fast_charge_support: bool = False


@dataclass
class HybridCar(AbstractCar):
    engine_capacity: float = 0.0
    battery_capacity: float = 0.0


class Fleet:
    def __init__(self, name: str):
        self.name = name
        self.cars: list[AbstractCar] = []

    def add_car(self, car: AbstractCar):
        self.cars.append(car)

    def __iter__(self):
        return iter(self.cars)


class Organization:
    def __init__(self, name: str, fleet: Fleet):
        self.name = name
        self.fleet = fleet


# ---------- LOGIC (фабрика и калькулятор) ----------

class CarFactory:
    """Фабрика для создания тестовых машин."""
    def create_ice_car(self) -> ICECar:
        return ICECar(
            brand="VW",
            model="Golf",
            base_price=15000,
            curb_weight=1200,
            engine_capacity=1.6,
            fuel_type="Petrol",
            emission_class="Euro 5",
        )

    def create_electric_car(self) -> ElectricCar:
        return ElectricCar(
            brand="Tesla",
            model="Model 3",
            base_price=35000,
            curb_weight=1700,
            max_range_km=420,
            fast_charge_support=True,
        )


class CarCalculator:
    """Простой калькулятор агрегатов по автопарку."""

    def total_price(self, cars):
        return sum(float(getattr(c, "base_price", 0) or 0) for c in cars)

    def avg_price(self, cars):
        return self.total_price(cars) / len(cars) if cars else 0.0

    def total_weight(self, cars):
        return sum(float(getattr(c, "curb_weight", 0) or 0) for c in cars)


DivisionCalculator = CarCalculator  # для совместимости с оригинальным кодом


# ---------- helpers (мелкие утилиты) ----------

def get(obj, name, default=None):
    """Безопасно достаёт атрибут 'name' у объекта 'obj', иначе возвращает default."""
    return getattr(obj, name, default)


def car_type(c):
    """Возвращает строковый тип авто для отображения в таблице."""
    if isinstance(c, ICECar):
        return "ICE"
    if isinstance(c, ElectricCar):
        return "EV"
    if isinstance(c, HybridCar):
        return "Hybrid"
    return c.__class__.__name__


def car_extra(c):
    """Собирает краткое описание «особых» полей по типу авто."""
    if isinstance(c, ICECar):
        parts = []
        if hasattr(c, "engine_capacity"):
            parts.append(f"{c.engine_capacity} L")
        if hasattr(c, "fuel_type"):
            parts.append(str(c.fuel_type))
        if hasattr(c, "emission_class"):
            parts.append(str(c.emission_class))
        return ", ".join(parts)
    if isinstance(c, ElectricCar):
        parts = []
        if hasattr(c, "max_range_km"):
            parts.append(f"{c.max_range_km} км")
        if hasattr(c, "fast_charge_support"):
            parts.append("FastCharge" if c.fast_charge_support else "No Fast")
        return ", ".join(parts)
    if isinstance(c, HybridCar):
        parts = []
        if hasattr(c, "engine_capacity"):
            parts.append(f"ICE {c.engine_capacity} L")
        if hasattr(c, "battery_capacity"):
            parts.append(f"Bat {c.battery_capacity} kWh")
        return ", ".join(parts)
    return ""


# ---------- Add/Edit dialog (диалог добавления/редактирования авто) ----------

class CarForm(tk.Toplevel):
    """Модальное окно для создания/редактирования объекта AbstractCar."""
    def __init__(self, master, initial: AbstractCar | None = None):
        super().__init__(master)
        self.title("Автомобиль")
        self.resizable(False, False)
        self.result: AbstractCar | None = None  # сюда положим готовый объект при OK

        # --- Выбор типа авто ---
        frm_type = ttk.Frame(self)
        frm_type.pack(fill="x", padx=10, pady=(10, 6))
        ttk.Label(frm_type, text="Тип:").pack(side="left")
        # Если редактируем существующий — подставим его тип; иначе ICE
        self.var_type = tk.StringVar(value=car_type(initial) if initial else "ICE")
        cmb = ttk.Combobox(
            frm_type,
            state="readonly",
            values=["ICE", "EV", "Hybrid"],
            textvariable=self.var_type,
            width=10,
        )
        cmb.pack(side="left", padx=6)
        cmb.bind("<<ComboboxSelected>>", lambda e: self._render_specific())

        # --- Общие поля ---
        frm_common = ttk.LabelFrame(self, text="Общее")
        frm_common.pack(fill="x", padx=10, pady=6)
        self.e_brand = self._entry(frm_common, "Бренд:", 0)
        self.e_model = self._entry(frm_common, "Модель:", 1)
        self.e_price = self._entry(frm_common, "Цена:", 2)
        self.e_weight = self._entry(frm_common, "Масса (кг):", 3)

        # --- Специфичные поля ---
        self.frm_spec = ttk.LabelFrame(self, text="Специфика")
        self.frm_spec.pack(fill="x", padx=10, pady=(0, 10))

        # --- Кнопки ---
        frm_btn = ttk.Frame(self)
        frm_btn.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(frm_btn, text="OK", command=self._ok).pack(side="right")
        ttk.Button(frm_btn, text="Отмена", command=self.destroy).pack(side="right", padx=6)

        # Если редактирование — подставляем значения
        if initial:
            self.e_brand.insert(0, get(initial, "brand", ""))
            self.e_model.insert(0, get(initial, "model", ""))
            self.e_price.insert(0, str(get(initial, "base_price", "") or ""))
            self.e_weight.insert(0, str(get(initial, "curb_weight", "") or ""))

        # Первичная отрисовка блока спецификации
        self._render_specific(initial)

        # Модальность
        self.transient(master)
        self.grab_set()
        self.wait_visibility()
        self.focus()

    @staticmethod
    def edit(master, entity: AbstractCar):
        return CarForm(master, initial=entity)

    def _entry(self, parent, label, row, width=28):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=6, pady=4)
        e = ttk.Entry(parent, width=width)
        e.grid(row=row, column=1, sticky="we", padx=6, pady=4)
        return e

    def _clear(self, parent):
        for w in parent.winfo_children():
            w.destroy()

    def _render_specific(self, initial=None):
        self._clear(self.frm_spec)
        t = self.var_type.get()
        if t == "ICE":
            self.s1 = self._entry(self.frm_spec, "Объём (л):", 0)
            self.s2 = self._entry(self.frm_spec, "Топливо:", 1)
            self.s3 = self._entry(self.frm_spec, "Экостандарт:", 2)
            if isinstance(initial, ICECar):
                self.s1.insert(0, str(get(initial, "engine_capacity", "") or ""))
                self.s2.insert(0, str(get(initial, "fuel_type", "") or ""))
                self.s3.insert(0, str(get(initial, "emission_class", "") or ""))
        elif t == "EV":
            self.s1 = self._entry(self.frm_spec, "Запас хода (км):", 0)
            self.s2 = self._entry(self.frm_spec, "Быстрая зарядка (0/1):", 1)
            if isinstance(initial, ElectricCar):
                self.s1.insert(0, str(get(initial, "max_range_km", "") or ""))
                self.s2.insert(0, "1" if get(initial, "fast_charge_support", False) else "0")
        else:
            # Hybrid
            self.s1 = self._entry(self.frm_spec, "Объём двигателя (л):", 0)
            self.s2 = self._entry(self.frm_spec, "Ёмкость батареи (кВт·ч):", 1)
            if isinstance(initial, HybridCar):
                self.s1.insert(0, str(get(initial, "engine_capacity", "") or ""))
                self.s2.insert(0, str(get(initial, "battery_capacity", "") or ""))

    def _ok(self):
        try:
            brand = self.e_brand.get().strip()
            model = self.e_model.get().strip()
            if not brand or not model:
                messagebox.showerror("Ошибка", "Бренд и модель обязательны")
                return

            base_price = float(self.e_price.get() or 0)
            curb_weight = float(self.e_weight.get() or 0)
            t = self.var_type.get()

            if t == "ICE":
                obj = ICECar(
                    brand=brand,
                    model=model,
                    base_price=base_price,
                    curb_weight=curb_weight,
                    engine_capacity=float(self.s1.get() or 0),
                    fuel_type=self.s2.get().strip(),
                    emission_class=self.s3.get().strip(),
                )
            elif t == "EV":
                obj = ElectricCar(
                    brand=brand,
                    model=model,
                    base_price=base_price,
                    curb_weight=curb_weight,
                    max_range_km=int(float(self.s1.get() or 0)),
                    fast_charge_support=self.s2.get().strip() in {"1", "true", "True", "yes", "да", "Да"},
                )
            else:
                obj = HybridCar(
                    brand=brand,
                    model=model,
                    base_price=base_price,
                    curb_weight=curb_weight,
                    engine_capacity=float(self.s1.get() or 0),
                    battery_capacity=float(self.s2.get() or 0),
                )

            self.result = obj
            self.destroy()
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректные числовые значения: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Проверьте поля: {e}")


# ---------- Main form (главное окно) ----------

class MainWindow(tk.Tk):
    """Главная форма приложения: таблица машин + CRUD + сводка."""
    def __init__(self):
        super().__init__()
        self.title("Управление автомобилями")
        self.geometry("960x560")

        # --- Модель и логика ---
        self.fleet = Fleet("Training Fleet")
        self.division = Organization("Учебное подразделение", self.fleet)
        self.factory = CarFactory()
        self.calculator = DivisionCalculator()

        # --- Начальные записи ---
        try:
            seed = [self.factory.create_ice_car(), self.factory.create_electric_car()]
            for c in seed:
                self._fleet_add(c)
        except Exception:
            pass

        self._build_widgets()
        self._refresh()
        self._update_summary()

    # ---- безопасные врапперы к Fleet ----
    def _fleet_items(self):
        if hasattr(self.fleet, "cars"):
            return self.fleet.cars
        if hasattr(self.fleet, "_cars"):
            return self.fleet._cars
        try:
            return list(iter(self.fleet))
        except Exception:
            return []

    def _fleet_add(self, car: AbstractCar):
        if hasattr(self.fleet, "add_car"):
            return self.fleet.add_car(car)
        if hasattr(self.fleet, "AddCar"):
            return self.fleet.AddCar(car)
        items = self._fleet_items()
        items.append(car)
        if hasattr(self.fleet, "cars"):
            self.fleet.cars = items
        elif hasattr(self.fleet, "_cars"):
            self.fleet._cars = items

    def _fleet_set_at(self, idx: int, car: AbstractCar):
        items = self._fleet_items()
        if 0 <= idx < len(items):
            items[idx] = car
            if hasattr(self.fleet, "cars"):
                self.fleet.cars = items
            elif hasattr(self.fleet, "_cars"):
                self.fleet._cars = items

    def _fleet_remove_at(self, idx: int):
        items = self._fleet_items()
        if 0 <= idx < len(items):
            del items[idx]
            if hasattr(self.fleet, "cars"):
                self.fleet.cars = items
            elif hasattr(self.fleet, "_cars"):
                self.fleet._cars = items

    # ---- UI ----
    def _build_widgets(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=10, pady=8)
        ttk.Button(bar, text="Добавить", command=self.on_add).pack(side="left")
        ttk.Button(bar, text="Редактировать", command=self.on_edit).pack(side="left", padx=6)
        ttk.Button(bar, text="Удалить", command=self.on_delete).pack(side="left")

        cols = ("type", "brand", "model", "price", "weight", "extra")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        self.tree.pack(fill="both", expand=True, padx=10)

        self.tree.heading("type", text="Тип")
        self.tree.heading("brand", text="Бренд")
        self.tree.heading("model", text="Модель")
        self.tree.heading("price", text="Цена")
        self.tree.heading("weight", text="Масса, кг")
        self.tree.heading("extra", text="Характеристики")

        for c, w in zip(cols, (90, 140, 160, 110, 110, 330)):
            self.tree.column(c, width=w, anchor="w")

        self.var_sum = tk.StringVar(master=self, value="")
        ttk.Label(self, textvariable=self.var_sum, anchor="w").pack(fill="x", padx=10, pady=6)

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        for i, car in enumerate(self._fleet_items()):
            self.tree.insert(
                "",
                "end",
                iid=str(i),
                values=(
                    car_type(car),
                    get(car, "brand", ""),
                    get(car, "model", ""),
                    get(car, "base_price", ""),
                    get(car, "curb_weight", ""),
                    car_extra(car),
                ),
            )

    def _sel_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    # ---- CRUD ----
    def on_add(self):
        dlg = CarForm(self)
        self.wait_window(dlg)
        if dlg.result:
            self._fleet_add(dlg.result)
            self._refresh()
            self._update_summary()

    def on_edit(self):
        idx = self._sel_index()
        if idx is None:
            messagebox.showinfo("Редактирование", "Выберите элемент")
            return
        current = self._fleet_items()[idx]
        dlg = CarForm.edit(self, current)
        self.wait_window(dlg)
        if dlg.result:
            self._fleet_set_at(idx, dlg.result)
            self._refresh()
            self._update_summary()

    def on_delete(self):
        idx = self._sel_index()
        if idx is None:
            messagebox.showinfo("Удаление", "Выберите элемент")
            return
        if not messagebox.askyesno("Подтверждение", "Удалить выбранный автомобиль?"):
            return
        self._fleet_remove_at(idx)
        self._refresh()
        self._update_summary()

    # ---- summary ----
    def _update_summary(self):
        cars = self._fleet_items()
        if self.calculator:
            try:
                total_price = self.calculator.total_price(cars)
                avg_price = self.calculator.avg_price(cars)
                total_weight = self.calculator.total_weight(cars)
                avg_weight = (total_weight / len(cars)) if cars else 0.0
            except Exception:
                total_price = sum(float(get(c, "base_price", 0) or 0) for c in cars)
                avg_price = (total_price / len(cars)) if cars else 0.0
                total_weight = sum(float(get(c, "curb_weight", 0) or 0) for c in cars)
                avg_weight = (total_weight / len(cars)) if cars else 0.0
        else:
            total_price = sum(float(get(c, "base_price", 0) or 0) for c in cars)
            avg_price = (total_price / len(cars)) if cars else 0.0
            total_weight = sum(float(get(c, "curb_weight", 0) or 0) for c in cars)
            avg_weight = (total_weight / len(cars)) if cars else 0.0

        ice_count = sum(isinstance(c, ICECar) for c in cars)
        ev_count = sum(isinstance(c, ElectricCar) for c in cars)
        hybrid_count = sum(isinstance(c, HybridCar) for c in cars)

        self.var_sum.set(
            f"Всего: {len(cars)} | "
            f"ICE: {ice_count} | EV: {ev_count} | Hybrid: {hybrid_count} | "
            f"Сумма цен: {total_price:.0f} | Ср. цена: {avg_price:.0f} | "
            f"Сумм. масса: {total_weight:.1f} кг | Ср. масса: {avg_weight:.1f} кг"
        )


# ---------- entry (точка входа) ----------
if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
