import pandas as pd


REQUIRED_COLUMNS = [
    "Import_Export",
    "Year",
    "Month",
    "TNVED",
    "Country",
    "US_dollars",
]

MONTH_NUMBERS = {
    "январь": 1,
    "февраль": 2,
    "март": 3,
    "апрель": 4,
    "май": 5,
    "июнь": 6,
    "июль": 7,
    "август": 8,
    "сентябрь": 9,
    "октябрь": 10,
    "ноябрь": 11,
    "декабрь": 12,
}

TRADE_TYPE_NAMES = {
    "Импорт": "Import",
    "Экспорт": "Export",
    "Import": "Import",
    "Export": "Export",
}


def preprocess_trade_data(data):
    # Подготавливаем загруженные данные к дальнейшим расчетам.
    data = data.copy()

    check_required_columns(data)
    data = drop_empty_rows(data)
    data = replace_month_with_number(data)
    data = normalize_trade_type(data)
    data = convert_column_types(data)
    data = remove_zero_value_rows(data)
    data = remove_invalid_tnved_rows(data)
    data = data.reset_index(drop=True)

    return data


def check_required_columns(data):
    # Проверяем наличие колонок, которые нужны для модели.
    missing_columns = []

    for column in REQUIRED_COLUMNS:
        if column not in data.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Отсутствуют обязательные колонки: {missing_columns}")


def drop_empty_rows(data):
    # Удаляем полностью пустые строки, если они есть в Excel-файле.
    data = data.dropna(how="all")
    return data


def replace_month_with_number(data):
    # Заменяем название месяца на номер месяца.
    month_names = data["Month"].astype(str).str.strip().str.lower()
    data["Month"] = month_names.map(MONTH_NUMBERS)

    if data["Month"].isna().any():
        raise ValueError("В колонке Month есть неизвестные названия месяцев")

    data["Month"] = data["Month"].astype(int)
    return data


def normalize_trade_type(data):
    # Приводим значения импорта и экспорта к единому виду.
    trade_type = data["Import_Export"].astype(str).str.strip()
    data["Import_Export"] = trade_type.map(TRADE_TYPE_NAMES)

    if data["Import_Export"].isna().any():
        raise ValueError("В колонке Import_Export есть неизвестные значения")

    return data


def convert_column_types(data):
    # Приводим колонки к типам, удобным для группировки и расчетов.
    data["Year"] = pd.to_numeric(data["Year"]).astype(int)
    data["TNVED"] = data["TNVED"].astype(str).str.strip()
    data["Country"] = data["Country"].astype(str).str.strip()
    data["US_dollars"] = pd.to_numeric(data["US_dollars"]).astype(float)

    return data


def remove_zero_value_rows(data):
    # Нулевые суммы не влияют на расчеты и могут создавать лишние группы.
    data = data[data["US_dollars"] != 0]
    return data


def remove_invalid_tnved_rows(data):
    # Код ТН ВЭД 0 не является товарной группой для ранжирования.
    data = data[data["TNVED"] != "0"]
    return data


def make_yearly_trade_table(data):
    # Собираем годовые суммы импорта и экспорта по каждому коду ТН ВЭД.
    grouped_data = data.groupby(
        ["TNVED", "Year", "Import_Export"],
        as_index=False,
    )["US_dollars"].sum()

    yearly_table = grouped_data.pivot_table(
        index=["TNVED", "Year"],
        columns="Import_Export",
        values="US_dollars",
        fill_value=0,
    ).reset_index()

    yearly_table.columns.name = None

    if "Import" not in yearly_table.columns:
        yearly_table["Import"] = 0.0

    if "Export" not in yearly_table.columns:
        yearly_table["Export"] = 0.0

    yearly_table = yearly_table[["TNVED", "Year", "Import", "Export"]]
    return yearly_table


def make_country_import_table(data):
    # Собираем импорт по странам для будущего расчета HHI.
    import_data = data[data["Import_Export"] == "Import"]

    country_table = import_data.groupby(
        ["TNVED", "Year", "Country"],
        as_index=False,
    )["US_dollars"].sum()

    country_table = country_table.rename(columns={"US_dollars": "Import_by_country"})
    return country_table
