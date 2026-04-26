import numpy as np
import pandas as pd


def calculate_indicators(yearly_trade, country_import, year, epsilon=1):
    # Рассчитываем все критерии для выбранного пользователем года.
    current_year = get_current_year_data(yearly_trade, year)
    previous_year = get_previous_year_import(yearly_trade, year)

    indicators = current_year.merge(previous_year, on="TNVED", how="left")
    indicators["Previous_Import"] = indicators["Previous_Import"].fillna(0)

    indicators = compute_import_share(indicators)
    indicators = compute_growth(indicators, epsilon)
    indicators = compute_ratio(indicators, epsilon)
    indicators = compute_hhi(indicators, country_import, year)

    indicators = indicators[["TNVED", "Year", "Import", "Export", "C1", "C2", "C3", "C4"]]
    return indicators


def get_current_year_data(yearly_trade, year):
    # Берем только выбранный год и исключаем группы без импорта.
    data = yearly_trade[yearly_trade["Year"] == year].copy()
    data = data[data["Import"] > 0]

    if data.empty:
        raise ValueError(f"Нет данных с импортом за выбранный год: {year}")

    return data


def get_previous_year_import(yearly_trade, year):
    # Берем импорт за предыдущий год для расчета динамики.
    previous_year = year - 1
    data = yearly_trade[yearly_trade["Year"] == previous_year].copy()
    data = data[["TNVED", "Import"]]
    data = data.rename(columns={"Import": "Previous_Import"})
    return data


def compute_import_share(data):
    # C1 = импорт группы / общий импорт за выбранный год.
    data = data.copy()
    total_import = data["Import"].sum()
    data["C1"] = data["Import"] / total_import
    return data


def compute_growth(data, epsilon=1):
    # C2 = ln((импорт текущего года + epsilon) / (импорт прошлого года + epsilon)).
    data = data.copy()
    data["C2"] = np.log((data["Import"] + epsilon) / (data["Previous_Import"] + epsilon))
    return data


def compute_ratio(data, epsilon=1):
    # C3 = импорт / (импорт + экспорт + epsilon).
    data = data.copy()
    data["C3"] = data["Import"] / (data["Import"] + data["Export"] + epsilon)
    return data


def compute_hhi(data, country_import, year):
    # C4 = сумма квадратов долей стран-поставщиков в импорте группы.
    data = data.copy()
    hhi = make_hhi_table(country_import, year)

    data = data.merge(hhi, on="TNVED", how="left")
    data["C4"] = data["C4"].fillna(0)

    return data


def make_hhi_table(country_import, year):
    # Готовим отдельную таблицу HHI по каждому коду ТН ВЭД.
    data = country_import[country_import["Year"] == year].copy()

    if data.empty:
        return pd.DataFrame(columns=["TNVED", "C4"])

    total_import = data.groupby("TNVED", as_index=False)["Import_by_country"].sum()
    total_import = total_import.rename(columns={"Import_by_country": "Total_Import"})

    data = data.merge(total_import, on="TNVED", how="left")
    data["Supplier_Share"] = data["Import_by_country"] / data["Total_Import"]
    data["Supplier_Share_Squared"] = data["Supplier_Share"] ** 2

    hhi = data.groupby("TNVED", as_index=False)["Supplier_Share_Squared"].sum()
    hhi = hhi.rename(columns={"Supplier_Share_Squared": "C4"})

    return hhi
