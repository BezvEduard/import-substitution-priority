from pathlib import Path

import pandas as pd


def export_ranking_to_excel(
    ranking,
    ahp_info,
    output_path,
    calculation_year=None,
    clipping_mode=None,
):
    # Сохраняем итоговый рейтинг и служебную информацию в Excel-файл.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    weights_table = make_weights_table(ahp_info)
    parameters_table = make_parameters_table(
        ahp_info,
        calculation_year,
        clipping_mode,
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        ranking.to_excel(writer, sheet_name="Ranking", index=False)
        weights_table.to_excel(writer, sheet_name="AHP Weights", index=False)
        parameters_table.to_excel(writer, sheet_name="Parameters", index=False)

    return output_path


def make_weights_table(ahp_info):
    # Преобразуем веса AHP в таблицу для отдельного листа Excel.
    weights = ahp_info["weights"]

    rows = []
    for criterion, weight in weights.items():
        rows.append(
            {
                "Criterion": criterion,
                "Weight": weight,
            }
        )

    return pd.DataFrame(rows)


def make_parameters_table(ahp_info, calculation_year=None, clipping_mode=None):
    # Собираем параметры расчета и показатели согласованности AHP.
    rows = [
        {"Parameter": "calculation_year", "Value": calculation_year},
        {"Parameter": "clipping_mode", "Value": clipping_mode},
        {"Parameter": "lambda_max", "Value": ahp_info["lambda_max"]},
        {"Parameter": "consistency_index", "Value": ahp_info["consistency_index"]},
        {"Parameter": "consistency_ratio", "Value": ahp_info["consistency_ratio"]},
        {"Parameter": "is_consistent", "Value": ahp_info["is_consistent"]},
    ]

    return pd.DataFrame(rows)
