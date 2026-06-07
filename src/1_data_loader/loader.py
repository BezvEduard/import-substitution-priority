import pandas as pd


def load_excel_data(file_path, sheet_name=0):
    # Загружаем Excel-файл без очистки и преобразования данных.
    data = pd.read_excel(file_path, sheet_name=sheet_name)
    return data
