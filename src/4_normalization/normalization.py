CRITERIA_COLUMNS = ["C1", "C2", "C3", "C4"]

CLIPPING_MODES = {
    "none": None,
    "1-99": (0.01, 0.99),
    "1-99 percentile": (0.01, 0.99),
    "5-95": (0.05, 0.95),
    "5-95 percentile": (0.05, 0.95),
}


def normalize_indicators(data, clipping_mode="none"):
    # Добавляем нормализованные значения критериев после выбранного клиппинга.
    check_criteria_columns(data)

    result = data.copy()
    clipped_data = apply_clipping(data, CRITERIA_COLUMNS, clipping_mode)
    normalized_data = min_max_normalize(clipped_data, CRITERIA_COLUMNS)

    for column in CRITERIA_COLUMNS:
        normalized_column = f"normalized_{column}"
        result[normalized_column] = normalized_data[normalized_column]

    return result


def apply_clipping(data, criteria_columns, clipping_mode="none"):
    # Ограничиваем выбросы по каждому критерию отдельно.
    if clipping_mode not in CLIPPING_MODES:
        raise ValueError(f"Неизвестный режим клиппинга: {clipping_mode}")

    percentile_range = CLIPPING_MODES[clipping_mode]
    clipped_data = data.copy()

    if percentile_range is None:
        return clipped_data

    lower_percentile, upper_percentile = percentile_range

    for column in criteria_columns:
        lower_value = clipped_data[column].quantile(lower_percentile)
        upper_value = clipped_data[column].quantile(upper_percentile)
        clipped_data[column] = clipped_data[column].clip(lower_value, upper_value)

    return clipped_data


def min_max_normalize(data, criteria_columns):
    # Приводим каждый критерий к диапазону от 0 до 1.
    normalized_data = data.copy()

    for column in criteria_columns:
        min_value = normalized_data[column].min()
        max_value = normalized_data[column].max()
        normalized_column = f"normalized_{column}"

        if max_value == min_value:
            normalized_data[normalized_column] = 0
        else:
            normalized_data[normalized_column] = (
                (normalized_data[column] - min_value) / (max_value - min_value)
            )

    return normalized_data


def check_criteria_columns(data):
    # Проверяем, что в таблице есть все критерии C1-C4.
    missing_columns = []

    for column in CRITERIA_COLUMNS:
        if column not in data.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Отсутствуют колонки критериев: {missing_columns}")
