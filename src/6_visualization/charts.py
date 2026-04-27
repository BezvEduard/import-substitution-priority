from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


CRITERIA_LABELS = {
    "C1": "Доля импорта",
    "C2": "Рост импорта",
    "C3": "Неконкурентоспособность",
    "C4": "Концентрация поставщиков",
}


def save_ranking_charts(
    ranking,
    model_info,
    output_dir="outputs",
    top_n=10,
    file_prefix="",
    components_figsize=(11, 6),
    dpi=150,
):
    # Сохраняем график вклада критериев в итоговый Score.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if file_prefix:
        components_path = output_dir / f"{file_prefix}_score_components.png"
    else:
        components_path = output_dir / "score_components.png"

    save_score_components_chart(ranking, model_info, components_path, top_n, components_figsize, dpi)

    return {
        "score_components": components_path,
    }


def save_score_components_chart(
    ranking,
    model_info,
    output_path,
    top_n=10,
    figsize=(11, 6),
    dpi=150,
):
    # Сохраняем один график: итоговый Score как сумму вкладов критериев.
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plot_score_components(ranking, model_info["weights"], output_path, top_n, figsize, dpi)
    return output_path


def plot_score_components(ranking, weights, output_path, top_n=10, figsize=(11, 6), dpi=150):
    # Показываем вклад нормализованных критериев в итоговый Score.
    top_data = ranking.head(top_n).copy()
    top_data = top_data.sort_values("Score", ascending=True)

    component_data = make_score_components(top_data, weights)

    plt.rcParams["font.family"] = "DejaVu Sans"
    fig, ax = plt.subplots(figsize=figsize)

    left = pd.Series(0, index=component_data.index, dtype=float)

    colors = {
        "C1": "#4C78A8",
        "C2": "#F58518",
        "C3": "#54A24B",
        "C4": "#B279A2",
    }

    for criterion in ["C1", "C2", "C3", "C4"]:
        ax.barh(
            component_data["TNVED"],
            component_data[criterion],
            left=left,
            label=f"{criterion} {CRITERIA_LABELS[criterion]}",
            color=colors[criterion],
        )
        left = left + component_data[criterion]

    ax.set_title(f"Вклад критериев в Score для top-{top_n}")
    ax.set_xlabel("Вклад в Score")
    ax.set_ylabel("TNVED")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="lower right", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi)
    plt.close(fig)


def make_score_components(data, weights):
    # Рассчитываем вклад каждого критерия в итоговую сумму WSM.
    components = pd.DataFrame()
    components["TNVED"] = data["TNVED"].astype(str)

    for criterion in ["C1", "C2", "C3", "C4"]:
        normalized_column = f"normalized_{criterion}"
        components[criterion] = data[normalized_column] * weights[criterion]

    return components
