from importlib import import_module


loader = import_module("src.1_data_loader.loader")
preprocessing = import_module("src.2_preprocessing.preprocessing")
indicators = import_module("src.3_indicators.indicators")


# Позже этот год будет выбираться пользователем в интерфейсе.
calculation_year = 2025

raw_data = loader.load_trade_data()
prepared_data = preprocessing.preprocess_trade_data(raw_data)
yearly_trade = preprocessing.make_yearly_trade_table(prepared_data)
country_import = preprocessing.make_country_import_table(prepared_data)
indicator_values = indicators.calculate_indicators(
    yearly_trade,
    country_import,
    calculation_year,
)

print(f"Критерии за {calculation_year} год:")
print(indicator_values.head())
print(indicator_values.info())
