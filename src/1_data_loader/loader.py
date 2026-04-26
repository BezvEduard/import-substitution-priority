import pandas as pd


def load_excel_data(file_path, sheet_name=0):
    # Загружаем Excel-файл без очистки и преобразования данных.
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    return data


def load_trade_data(file_path="data/trade.xlsx"):
    # Загружаем основной файл с внешнеторговыми данными.
    data = load_excel_data(file_path)
    return data
