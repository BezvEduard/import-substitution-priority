from importlib import import_module


loader = import_module("src.1_data_loader.loader")
preprocessing = import_module("src.2_preprocessing.preprocessing")


raw_data = loader.load_trade_data()
prepared_data = preprocessing.preprocess_trade_data(raw_data)
yearly_trade = preprocessing.make_yearly_trade_table(prepared_data)
country_import = preprocessing.make_country_import_table(prepared_data)

print("Подготовленные данные:")
print(prepared_data.head())
print(prepared_data.info())

print("\nГодовая таблица Import/Export:")
print(yearly_trade.head())

print("\nИмпорт по странам:")
print(country_import.head())
