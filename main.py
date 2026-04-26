from importlib import import_module


loader = import_module("src.1_data_loader.loader")
preprocessing = import_module("src.2_preprocessing.preprocessing")
indicators = import_module("src.3_indicators.indicators")
normalization = import_module("src.4_normalization.normalization")
model = import_module("src.5_model.model")
exporter = import_module("src.7_export.exporter")


# Позже этот год будет выбираться пользователем в интерфейсе.
calculation_year = 2025
clipping_mode = "1-99"

raw_data = loader.load_trade_data()
prepared_data = preprocessing.preprocess_trade_data(raw_data)
yearly_trade = preprocessing.make_yearly_trade_table(prepared_data)
country_import = preprocessing.make_country_import_table(prepared_data)

indicator_values = indicators.calculate_indicators(
    yearly_trade,
    country_import,
    calculation_year,
)

normalized_values = normalization.normalize_indicators(
    indicator_values,
    clipping_mode,
)

ranking, ahp_info = model.calculate_priority_ranking(normalized_values)

print("AHP weights:")
print(ahp_info["weights"])
print("Consistency ratio:", ahp_info["consistency_ratio"])

print(f"\nPriority ranking for {calculation_year}:")
print(ranking.head())
print(ranking.info())

output_path = exporter.export_ranking_to_excel(
    ranking,
    ahp_info,
    f"outputs/ranking_{calculation_year}.xlsx",
    calculation_year,
    clipping_mode,
)

print(f"\nExcel export saved to: {output_path}")
