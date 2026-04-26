import numpy as np


CRITERIA = ["C1", "C2", "C3", "C4"]

NORMALIZED_COLUMNS = {
    "C1": "normalized_C1",
    "C2": "normalized_C2",
    "C3": "normalized_C3",
    "C4": "normalized_C4",
}

RANDOM_INDEX = {
    1: 0.00,
    2: 0.00,
    3: 0.58,
    4: 0.90,
}


def get_default_pairwise_matrix():
    # Временная экспертная матрица. Позже ее будет заполнять пользователь.
    matrix = np.array(
        [
            [1, 3, 2, 2],
            [1 / 3, 1, 1 / 2, 1 / 2],
            [1 / 2, 2, 1, 1],
            [1 / 2, 2, 1, 1],
        ],
        dtype=float,
    )
    return matrix


def calculate_ahp_weights(pairwise_matrix=None):
    # Рассчитываем веса критериев методом AHP.
    if pairwise_matrix is None:
        pairwise_matrix = get_default_pairwise_matrix()

    matrix = np.array(pairwise_matrix, dtype=float)
    check_pairwise_matrix(matrix)

    column_sums = matrix.sum(axis=0)
    normalized_matrix = matrix / column_sums
    weight_values = normalized_matrix.mean(axis=1)

    weights = {}
    for criterion, weight in zip(CRITERIA, weight_values):
        weights[criterion] = float(weight)

    consistency = calculate_consistency_ratio(matrix, weight_values)

    ahp_info = {
        "weights": weights,
        "lambda_max": float(consistency["lambda_max"]),
        "consistency_index": float(consistency["consistency_index"]),
        "consistency_ratio": float(consistency["consistency_ratio"]),
        "is_consistent": consistency["consistency_ratio"] <= 0.10,
    }

    return weights, ahp_info


def check_pairwise_matrix(matrix):
    # Проверяем базовые требования к матрице попарных сравнений.
    expected_size = len(CRITERIA)

    if matrix.shape != (expected_size, expected_size):
        raise ValueError("Матрица попарных сравнений должна быть размером 4x4")

    if (matrix <= 0).any():
        raise ValueError("Все значения матрицы попарных сравнений должны быть положительными")

    if not np.allclose(np.diag(matrix), 1):
        raise ValueError("На диагонали матрицы попарных сравнений должны быть единицы")

    if not np.allclose(matrix * matrix.T, 1):
        raise ValueError("Матрица попарных сравнений должна быть взаимно обратной")


def calculate_consistency_ratio(matrix, weight_values):
    # Рассчитываем показатели согласованности AHP.
    criteria_count = len(weight_values)
    weighted_sum = matrix @ weight_values
    lambda_values = weighted_sum / weight_values
    lambda_max = lambda_values.mean()

    consistency_index = (lambda_max - criteria_count) / (criteria_count - 1)
    random_index = RANDOM_INDEX[criteria_count]

    if random_index == 0:
        consistency_ratio = 0
    else:
        consistency_ratio = consistency_index / random_index

    return {
        "lambda_max": lambda_max,
        "consistency_index": consistency_index,
        "consistency_ratio": consistency_ratio,
    }


def calculate_priority_ranking(data, pairwise_matrix=None):
    # Считаем AHP-веса, итоговый Score и ранг товарных групп.
    weights, ahp_info = calculate_ahp_weights(pairwise_matrix)
    ranking = calculate_score(data, weights)
    ranking = add_rank(ranking)

    return ranking, ahp_info


def calculate_priority_ranking_with_weights(data, weights):
    # Считаем итоговый Score и ранг с вручную заданными весами.
    check_weights(weights)
    ranking = calculate_score(data, weights)
    ranking = add_rank(ranking)

    model_info = {
        "weights": weights,
        "lambda_max": None,
        "consistency_index": None,
        "consistency_ratio": None,
        "is_consistent": None,
        "weight_method": "manual",
    }

    return ranking, model_info


def calculate_score(data, weights):
    # Score = сумма произведений нормализованных критериев на их веса.
    check_normalized_columns(data)
    check_weights(weights)

    result = data.copy()
    result["Score"] = 0.0

    for criterion in CRITERIA:
        normalized_column = NORMALIZED_COLUMNS[criterion]
        result["Score"] = result["Score"] + result[normalized_column] * weights[criterion]

    return result


def add_rank(data):
    # Dense-ранг: одинаковый Score получает одинаковый ранг без пропусков.
    result = data.copy()
    result["Rank"] = result["Score"].rank(method="dense", ascending=False).astype(int)
    result = result.sort_values(["Rank", "Score"], ascending=[True, False])
    result = result.reset_index(drop=True)
    return result


def check_normalized_columns(data):
    # Проверяем наличие нормализованных критериев.
    missing_columns = []

    for column in NORMALIZED_COLUMNS.values():
        if column not in data.columns:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(f"Отсутствуют нормализованные критерии: {missing_columns}")


def check_weights(weights):
    # Проверяем веса перед расчетом WSM.
    missing_weights = []

    for criterion in CRITERIA:
        if criterion not in weights:
            missing_weights.append(criterion)

    if missing_weights:
        raise ValueError(f"Отсутствуют веса критериев: {missing_weights}")

    total_weight = sum(weights.values())

    if not np.isclose(total_weight, 1):
        raise ValueError("Сумма весов критериев должна быть равна 1")
