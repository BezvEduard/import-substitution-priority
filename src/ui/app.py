from importlib import import_module
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


loader = import_module("src.1_data_loader.loader")
preprocessing = import_module("src.2_preprocessing.preprocessing")
indicators = import_module("src.3_indicators.indicators")
normalization = import_module("src.4_normalization.normalization")
model = import_module("src.5_model.model")
exporter = import_module("src.7_export.exporter")


CRITERIA_LABELS = {
    "C1": "C1 Import Share",
    "C2": "C2 Growth",
    "C3": "C3 Import Ratio",
    "C4": "C4 HHI",
}


class ImportSubstitutionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Import Substitution Priority")
        self.root.geometry("1280x780")

        self.file_path = tk.StringVar(value="data/trade.xlsx")
        self.year = tk.StringVar(value="2025")
        self.clipping_mode = tk.StringVar(value="1-99")
        self.weight_method = tk.StringVar(value="AHP")
        self.status = tk.StringVar(value="Выберите файл и запустите расчет")
        self.summary = tk.StringVar(value="")

        self.ranking = None
        self.ahp_info = None
        self.ahp_entries = {}
        self.ahp_inverse_labels = {}
        self.manual_weight_vars = {}

        self.create_widgets()
        self.fill_default_ahp_matrix()
        self.update_year_options()

    def create_widgets(self):
        controls = ttk.Frame(self.root, padding=10)
        controls.pack(fill="x")

        ttk.Label(controls, text="Файл данных").grid(row=0, column=0, sticky="w")
        file_entry = ttk.Entry(controls, textvariable=self.file_path, width=70)
        file_entry.grid(row=0, column=1, padx=6, sticky="we")

        browse_button = ttk.Button(controls, text="Выбрать", command=self.choose_file)
        browse_button.grid(row=0, column=2, padx=6)

        ttk.Label(controls, text="Год").grid(row=0, column=3, padx=(18, 0), sticky="w")
        self.year_box = ttk.Combobox(controls, textvariable=self.year, width=10, state="readonly")
        self.year_box.grid(row=0, column=4, padx=6)

        ttk.Label(controls, text="Клиппинг").grid(row=0, column=5, padx=(18, 0), sticky="w")
        clipping_box = ttk.Combobox(
            controls,
            textvariable=self.clipping_mode,
            values=["none", "1-99", "5-95"],
            width=14,
            state="readonly",
        )
        clipping_box.grid(row=0, column=6, padx=6)

        ttk.Label(controls, text="Метод весов").grid(row=0, column=7, padx=(18, 0), sticky="w")
        weight_method_box = ttk.Combobox(
            controls,
            textvariable=self.weight_method,
            values=["AHP", "manual"],
            width=10,
            state="readonly",
        )
        weight_method_box.grid(row=0, column=8, padx=6)
        weight_method_box.bind("<<ComboboxSelected>>", self.update_weight_input_visibility)

        calculate_button = ttk.Button(controls, text="Рассчитать", command=self.calculate)
        calculate_button.grid(row=0, column=9, padx=(18, 6))

        export_button = ttk.Button(controls, text="Экспорт Excel", command=self.export_excel)
        export_button.grid(row=0, column=10, padx=6)

        controls.columnconfigure(1, weight=1)

        self.create_ahp_widgets()
        self.create_manual_weight_widgets()
        self.update_weight_input_visibility()

        info = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        info.pack(fill="x")

        ttk.Label(info, textvariable=self.status).pack(anchor="w")
        ttk.Label(info, textvariable=self.summary).pack(anchor="w")

        self.create_ranking_table()

    def create_ahp_widgets(self):
        self.ahp_frame = ttk.LabelFrame(self.root, text="Матрица попарных сравнений AHP", padding=10)
        ahp_frame = self.ahp_frame

        ttk.Label(
            ahp_frame,
            text="Заполняются значения выше диагонали. Нижняя часть матрицы рассчитывается автоматически.",
        ).grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))

        reset_button = ttk.Button(
            ahp_frame,
            text="Сбросить матрицу",
            command=self.fill_default_ahp_matrix,
        )
        reset_button.grid(row=0, column=6, sticky="e", padx=(12, 0), pady=(0, 8))

        criteria = model.CRITERIA

        ttk.Label(ahp_frame, text="").grid(row=1, column=0, sticky="nsew")
        for column_index, criterion in enumerate(criteria, start=1):
            ttk.Label(
                ahp_frame,
                text=CRITERIA_LABELS[criterion],
                anchor="center",
            ).grid(row=1, column=column_index, padx=4, pady=2, sticky="nsew")

        for row_index, row_criterion in enumerate(criteria, start=2):
            ttk.Label(
                ahp_frame,
                text=CRITERIA_LABELS[row_criterion],
                anchor="w",
            ).grid(row=row_index, column=0, padx=4, pady=2, sticky="w")

            for column_index, column_criterion in enumerate(criteria, start=1):
                matrix_row = row_index - 2
                matrix_column = column_index - 1

                if matrix_row == matrix_column:
                    ttk.Label(ahp_frame, text="1", anchor="center").grid(
                        row=row_index,
                        column=column_index,
                        padx=4,
                        pady=2,
                        sticky="nsew",
                    )
                elif matrix_row < matrix_column:
                    entry = ttk.Entry(ahp_frame, width=10, justify="center")
                    entry.grid(row=row_index, column=column_index, padx=4, pady=2)
                    entry.bind("<KeyRelease>", self.update_ahp_inverse_labels)
                    entry.bind("<FocusOut>", self.update_ahp_inverse_labels)
                    self.ahp_entries[(matrix_row, matrix_column)] = entry
                else:
                    label = ttk.Label(ahp_frame, text="", anchor="center")
                    label.grid(
                        row=row_index,
                        column=column_index,
                        padx=4,
                        pady=2,
                        sticky="nsew",
                    )
                    self.ahp_inverse_labels[(matrix_row, matrix_column)] = label

        for column_index in range(7):
            ahp_frame.columnconfigure(column_index, weight=1)

    def create_manual_weight_widgets(self):
        self.weights_frame = ttk.LabelFrame(self.root, text="Ручные веса критериев", padding=10)
        weights_frame = self.weights_frame

        ttk.Label(
            weights_frame,
            text="Используются при методе весов manual. Сумма весов должна быть равна 1.",
        ).grid(row=0, column=0, columnspan=8, sticky="w", pady=(0, 8))

        default_weights = {
            "C1": "0.25",
            "C2": "0.25",
            "C3": "0.25",
            "C4": "0.25",
        }

        for column_index, criterion in enumerate(model.CRITERIA):
            ttk.Label(weights_frame, text=CRITERIA_LABELS[criterion]).grid(
                row=1,
                column=column_index * 2,
                padx=(0, 4),
                sticky="w",
            )

            variable = tk.StringVar(value=default_weights[criterion])
            entry = ttk.Entry(weights_frame, textvariable=variable, width=10, justify="center")
            entry.grid(row=1, column=column_index * 2 + 1, padx=(0, 12), sticky="w")
            self.manual_weight_vars[criterion] = variable

        equal_button = ttk.Button(
            weights_frame,
            text="Равные веса",
            command=self.fill_equal_manual_weights,
        )
        equal_button.grid(row=1, column=8, padx=(8, 0), sticky="w")

    def update_weight_input_visibility(self, event=None):
        if self.weight_method.get() == "manual":
            self.ahp_frame.pack_forget()
            self.weights_frame.pack(fill="x", padx=10, pady=(0, 8), after=self.root.winfo_children()[0])
        else:
            self.weights_frame.pack_forget()
            self.ahp_frame.pack(fill="x", padx=10, pady=(0, 8), after=self.root.winfo_children()[0])

    def create_ranking_table(self):
        table_frame = ttk.Frame(self.root, padding=10)
        table_frame.pack(fill="both", expand=True)

        columns = [
            "Rank",
            "TNVED",
            "Score",
            "Import",
            "Export",
            "C1",
            "C2",
            "C3",
            "C4",
        ]

        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        column_widths = {
            "Rank": 70,
            "TNVED": 110,
            "Score": 110,
            "Import": 150,
            "Export": 150,
            "C1": 100,
            "C2": 100,
            "C3": 100,
            "C4": 100,
        }

        for column in columns:
            self.table.heading(column, text=column)
            self.table.column(column, width=column_widths[column], anchor="center")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def choose_file(self):
        path = filedialog.askopenfilename(
            title="Выберите файл данных",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
        )

        if path:
            self.file_path.set(path)
            self.update_year_options()

    def update_year_options(self):
        path = Path(self.file_path.get())

        if not path.exists():
            return

        try:
            raw_data = loader.load_trade_data(path)
            prepared_data = preprocessing.preprocess_trade_data(raw_data)
            years = sorted(prepared_data["Year"].unique())
            years = [str(year) for year in years]

            self.year_box["values"] = years
            if self.year.get() not in years and years:
                self.year.set(years[-1])
        except Exception as error:
            messagebox.showerror("Ошибка загрузки годов", str(error))

    def fill_default_ahp_matrix(self):
        default_matrix = model.get_default_pairwise_matrix()

        for (row_index, column_index), entry in self.ahp_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, self.format_matrix_value(default_matrix[row_index][column_index]))

        self.update_ahp_inverse_labels()

    def update_ahp_inverse_labels(self, event=None):
        for (row_index, column_index), label in self.ahp_inverse_labels.items():
            source_entry = self.ahp_entries[(column_index, row_index)]

            try:
                value = self.parse_comparison_value(source_entry.get())
                inverse_value = 1 / value
                label.config(text=self.format_matrix_value(inverse_value))
            except ValueError:
                label.config(text="ошибка")

    def get_pairwise_matrix(self):
        criteria_count = len(model.CRITERIA)
        matrix = [[1.0 for _ in range(criteria_count)] for _ in range(criteria_count)]

        for (row_index, column_index), entry in self.ahp_entries.items():
            value = self.parse_comparison_value(entry.get())
            matrix[row_index][column_index] = value
            matrix[column_index][row_index] = 1 / value

        return matrix

    def get_manual_weights(self):
        weights = {}

        for criterion, variable in self.manual_weight_vars.items():
            weights[criterion] = self.parse_weight_value(variable.get())

        model.check_weights(weights)
        return weights

    def parse_weight_value(self, raw_value):
        value = raw_value.strip().replace(",", ".")
        number = float(value)

        if number < 0:
            raise ValueError("Вес критерия не может быть отрицательным")

        return number

    def fill_equal_manual_weights(self):
        for variable in self.manual_weight_vars.values():
            variable.set("0.25")

    def parse_comparison_value(self, raw_value):
        value = raw_value.strip().replace(",", ".")

        if "/" in value:
            numerator, denominator = value.split("/", 1)
            number = float(numerator) / float(denominator)
        else:
            number = float(value)

        if number <= 0:
            raise ValueError("Значения матрицы AHP должны быть положительными")

        return number

    def format_matrix_value(self, value):
        if abs(value - round(value)) < 0.000001:
            return str(int(round(value)))

        return f"{value:.4f}".rstrip("0").rstrip(".")

    def calculate(self):
        try:
            path = Path(self.file_path.get())
            calculation_year = int(self.year.get())
            clipping_mode = self.clipping_mode.get()
            weight_method = self.weight_method.get()

            self.status.set("Выполняется расчет...")
            self.root.update_idletasks()

            raw_data = loader.load_trade_data(path)
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

            if weight_method == "manual":
                weights = self.get_manual_weights()
                self.ranking, self.ahp_info = model.calculate_priority_ranking_with_weights(
                    normalized_values,
                    weights,
                )
            else:
                pairwise_matrix = self.get_pairwise_matrix()
                self.ranking, self.ahp_info = model.calculate_priority_ranking(
                    normalized_values,
                    pairwise_matrix,
                )
                self.ahp_info["weight_method"] = "AHP"

            self.update_table()
            self.update_summary(calculation_year, clipping_mode)
        except Exception as error:
            self.status.set("Ошибка расчета")
            messagebox.showerror("Ошибка расчета", str(error))

    def update_table(self):
        for item in self.table.get_children():
            self.table.delete(item)

        for _, row in self.ranking.iterrows():
            self.table.insert(
                "",
                "end",
                values=[
                    int(row["Rank"]),
                    row["TNVED"],
                    f"{row['Score']:.6f}",
                    f"{row['Import']:.2f}",
                    f"{row['Export']:.2f}",
                    f"{row['C1']:.6f}",
                    f"{row['C2']:.6f}",
                    f"{row['C3']:.6f}",
                    f"{row['C4']:.6f}",
                ],
            )

    def update_summary(self, calculation_year, clipping_mode):
        weights = self.ahp_info["weights"]
        consistency_ratio = self.ahp_info["consistency_ratio"]
        weight_method = self.ahp_info.get("weight_method", self.weight_method.get())

        self.status.set(
            f"Расчет завершен: год {calculation_year}, строк рейтинга {len(self.ranking)}"
        )

        if consistency_ratio is None:
            consistency_summary = "CR: не рассчитывается"
        else:
            consistency_text = "согласована" if self.ahp_info["is_consistent"] else "не согласована"
            consistency_summary = f"CR: {consistency_ratio:.4f} ({consistency_text})"

        self.summary.set(
            " | ".join(
                [
                    f"clipping: {clipping_mode}",
                    f"weights: {weight_method}",
                    f"C1: {weights['C1']:.4f}",
                    f"C2: {weights['C2']:.4f}",
                    f"C3: {weights['C3']:.4f}",
                    f"C4: {weights['C4']:.4f}",
                    consistency_summary,
                ]
            )
        )

    def export_excel(self):
        if self.ranking is None or self.ahp_info is None:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет")
            return

        calculation_year = int(self.year.get())
        clipping_mode = self.clipping_mode.get()
        weight_method = self.ahp_info.get("weight_method", self.weight_method.get())

        output_path = filedialog.asksaveasfilename(
            title="Сохранить рейтинг",
            initialdir="outputs",
            initialfile=f"ranking_{calculation_year}.xlsx",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
        )

        if not output_path:
            return

        try:
            saved_path = exporter.export_ranking_to_excel(
                self.ranking,
                self.ahp_info,
                output_path,
                calculation_year,
                clipping_mode,
                weight_method,
            )
            self.status.set(f"Excel сохранен: {saved_path}")
            messagebox.showinfo("Экспорт завершен", f"Файл сохранен:\n{saved_path}")
        except Exception as error:
            messagebox.showerror("Ошибка экспорта", str(error))


def run_app():
    root = tk.Tk()
    app = ImportSubstitutionApp(root)
    root.mainloop()
    return app
