from importlib import import_module
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


loader = import_module("src.1_data_loader.loader")
preprocessing = import_module("src.2_preprocessing.preprocessing")
indicators = import_module("src.3_indicators.indicators")
normalization = import_module("src.4_normalization.normalization")
model = import_module("src.5_model.model")
charts = import_module("src.6_visualization.charts")
exporter = import_module("src.7_export.exporter")


CRITERIA_LABELS = {
    "C1": "C1 Доля импорта",
    "C2": "C2 Рост импорта",
    "C3": "C3 Неконкурентоспособность",
    "C4": "C4 Концентрация поставщиков",
}


class ImportSubstitutionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Import Substitution Priority")
        self.root.geometry("1280x780")
        self.maximize_window()

        self.file_path = tk.StringVar(value="")
        self.year = tk.StringVar(value="2025")
        self.clipping_mode = tk.StringVar(value="1-99")
        self.weight_method = tk.StringVar(value="AHP")
        self.status = tk.StringVar(value="Выберите файл и запустите расчет")
        self.summary_parameters = tk.StringVar(value="")
        self.summary_weights = tk.StringVar(value="")

        self.ranking = None
        self.ahp_info = None
        self.ahp_entries = {}
        self.ahp_inverse_labels = {}
        self.manual_weight_vars = {}
        self.expert_count = tk.StringVar(value="1")
        self.manual_expert_rows = []
        self.chart_images = {}
        self.ahp_preview = tk.StringVar(value="Можете предварительно рассчитать веса")
        self.result_panes = None
        self.table_columns = []
        self.table_headings = {}
        self.table_min_column_widths = {}
        self.sort_column = None
        self.sort_descending = True

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

        calculate_button = tk.Button(
            controls,
            text="\u0420\u0430\u0441\u0441\u0447\u0438\u0442\u0430\u0442\u044c",
            command=self.calculate,
            bg="#D9EAFD",
            activebackground="#C8DCF5",
        )
        calculate_button.grid(row=0, column=9, padx=(18, 6))

        export_button = ttk.Button(controls, text="Экспорт Excel", command=self.export_excel)
        export_button.grid(row=0, column=10, padx=6)

        charts_button = ttk.Button(controls, text="Экспорт графиков", command=self.save_charts)
        charts_button.grid(row=0, column=11, padx=6)

        controls.columnconfigure(1, weight=1)

        self.create_ahp_widgets()
        self.create_manual_weight_widgets()
        self.update_weight_input_visibility()

        info = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        info.pack(fill="x")

        ttk.Label(info, textvariable=self.status).pack(anchor="w")
        ttk.Label(info, textvariable=self.summary_parameters).pack(anchor="w")
        ttk.Label(info, textvariable=self.summary_weights).pack(anchor="w")

        self.create_ranking_table()

    def maximize_window(self):
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)

    def create_ahp_widgets(self):
        self.ahp_frame = ttk.LabelFrame(self.root, padding=10)
        ahp_frame = self.ahp_frame

        title_frame = ttk.Frame(ahp_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(title_frame, text="Матрица попарных сравнений AHP").pack(side="left")
        ttk.Button(
            title_frame,
            text="?",
            width=2,
            command=self.show_ahp_help,
        ).pack(side="left", padx=(6, 0))

        matrix_frame = ttk.Frame(ahp_frame)
        matrix_frame.grid(row=1, column=0, sticky="nw")

        legend_frame = ttk.LabelFrame(ahp_frame, text="Критерии", padding=8)
        legend_frame.grid(row=1, column=1, padx=(18, 0), sticky="nw")

        criteria = model.CRITERIA

        ttk.Label(matrix_frame, text="").grid(row=0, column=0, sticky="nsew")
        for column_index, criterion in enumerate(criteria, start=1):
            ttk.Label(
                matrix_frame,
                text=criterion,
                anchor="center",
                justify="center",
                width=6,
            ).grid(row=0, column=column_index, padx=3, pady=2, sticky="nsew")

        for row_index, row_criterion in enumerate(criteria, start=1):
            ttk.Label(
                matrix_frame,
                text=row_criterion,
                anchor="center",
                width=6,
            ).grid(row=row_index, column=0, padx=3, pady=2, sticky="nsew")

            for column_index, column_criterion in enumerate(criteria, start=1):
                matrix_row = row_index - 1
                matrix_column = column_index - 1

                if matrix_row == matrix_column:
                    ttk.Label(matrix_frame, text="1", anchor="center", width=6).grid(
                        row=row_index,
                        column=column_index,
                        padx=3,
                        pady=2,
                        sticky="nsew",
                    )
                elif matrix_row < matrix_column:
                    entry = ttk.Entry(matrix_frame, width=6, justify="center")
                    entry.grid(row=row_index, column=column_index, padx=3, pady=2)
                    entry.bind("<KeyRelease>", self.update_ahp_inverse_labels)
                    entry.bind("<FocusOut>", self.update_ahp_inverse_labels)
                    self.ahp_entries[(matrix_row, matrix_column)] = entry
                else:
                    label = ttk.Label(matrix_frame, text="", anchor="center", width=6)
                    label.grid(
                        row=row_index,
                        column=column_index,
                        padx=3,
                        pady=2,
                        sticky="nsew",
                    )
                    self.ahp_inverse_labels[(matrix_row, matrix_column)] = label

        buttons_frame = ttk.Frame(matrix_frame)
        buttons_frame.grid(row=5, column=0, columnspan=5, sticky="w", pady=(8, 0))

        reset_button = ttk.Button(
            buttons_frame,
            text="Сбросить матрицу",
            command=self.reset_ahp_matrix,
        )
        reset_button.pack(side="left")

        preview_button = ttk.Button(
            buttons_frame,
            text="Рассчитать веса",
            command=self.preview_ahp_weights,
        )
        preview_button.pack(side="left", padx=(8, 0))

        ttk.Label(
            ahp_frame,
            textvariable=self.ahp_preview,
            anchor="w",
            justify="left",
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

        for row_index, criterion in enumerate(criteria):
            ttk.Label(
                legend_frame,
                text=CRITERIA_LABELS[criterion],
                anchor="w",
            ).grid(row=row_index, column=0, sticky="w", pady=1)

        for column_index in range(5):
            matrix_frame.columnconfigure(column_index, weight=0)

        ahp_frame.columnconfigure(0, weight=0)
        ahp_frame.columnconfigure(1, weight=0)

    def show_ahp_help(self):
        messagebox.showinfo(
            "Подсказка по AHP",
            "В матрице сравниваются критерии между собой.\n\n"
            "Значение в ячейке показывает, во сколько раз критерий слева важнее критерия сверху.\n\n"
            "Например, 3 в строке C1 и столбце C2 означает: C1 важнее C2 в 3 раза. "
            "Значение 1 означает равную важность.\n\n"
            "Заполняется только верхняя часть матрицы. Нижняя часть считается автоматически обратными значениями: "
            "если C1/C2 = 3, то C2/C1 = 1/3."
        )

    def create_manual_weight_widgets(self):
        self.weights_frame = ttk.LabelFrame(self.root, padding=10)
        weights_frame = self.weights_frame

        title_frame = ttk.Frame(weights_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(title_frame, text="Ручные веса критериев").pack(side="left")

        settings_frame = ttk.Frame(weights_frame)
        settings_frame.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(settings_frame, text="Количество экспертов").pack(side="left")
        expert_count_box = ttk.Combobox(
            settings_frame,
            textvariable=self.expert_count,
            values=["1", "2", "3", "4"],
            width=5,
            state="readonly",
        )
        expert_count_box.pack(side="left", padx=(6, 0))
        expert_count_box.bind("<<ComboboxSelected>>", self.update_manual_expert_visibility)

        input_frame = ttk.Frame(weights_frame)
        input_frame.grid(row=2, column=0, sticky="nw")

        legend_frame = ttk.LabelFrame(weights_frame, text="Критерии", padding=8)
        legend_frame.grid(row=2, column=1, padx=(18, 0), sticky="nw")

        default_weights = {
            "C1": "0.25",
            "C2": "0.25",
            "C3": "0.25",
            "C4": "0.25",
        }

        ttk.Label(input_frame, text="", width=10).grid(row=0, column=0, padx=3, pady=(0, 2))
        for column_index, criterion in enumerate(model.CRITERIA, start=1):
            ttk.Label(
                input_frame,
                text=criterion,
                anchor="center",
                width=7,
            ).grid(row=0, column=column_index, padx=3, pady=(0, 2), sticky="nsew")

        for expert_index in range(4):
            row_widgets = []
            expert_label = ttk.Label(
                input_frame,
                text=f"Эксперт {expert_index + 1}",
                anchor="w",
                width=10,
            )
            expert_label.grid(row=expert_index + 1, column=0, padx=3, pady=2, sticky="w")
            row_widgets.append(expert_label)

            for column_index, criterion in enumerate(model.CRITERIA, start=1):
                variable = tk.StringVar(value=default_weights[criterion])
                entry = ttk.Entry(input_frame, textvariable=variable, width=7, justify="center")
                entry.grid(row=expert_index + 1, column=column_index, padx=3, pady=2)
                self.manual_weight_vars[(expert_index, criterion)] = variable
                row_widgets.append(entry)

            self.manual_expert_rows.append(row_widgets)

        equal_button = ttk.Button(
            input_frame,
            text="Равные веса",
            command=self.fill_equal_manual_weights,
        )
        equal_button.grid(row=5, column=0, columnspan=5, sticky="w", pady=(8, 0))

        for row_index, criterion in enumerate(model.CRITERIA):
            ttk.Label(
                legend_frame,
                text=CRITERIA_LABELS[criterion],
                anchor="w",
            ).grid(row=row_index, column=0, sticky="w", pady=1)

        for column_index in range(5):
            input_frame.columnconfigure(column_index, weight=0)

        weights_frame.columnconfigure(0, weight=0)
        weights_frame.columnconfigure(1, weight=0)
        self.update_manual_expert_visibility()

    def update_manual_expert_visibility(self, event=None):
        expert_count = int(self.expert_count.get())

        for expert_index, row_widgets in enumerate(self.manual_expert_rows):
            for widget in row_widgets:
                if expert_index < expert_count:
                    widget.grid()
                else:
                    widget.grid_remove()

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

        headings = {
            "Rank": "Rank",
            "TNVED": "TNVED",
            "Score": "Score",
            "Import": "Import",
            "Export": "Export",
            "C1": CRITERIA_LABELS["C1"],
            "C2": CRITERIA_LABELS["C2"],
            "C3": CRITERIA_LABELS["C3"],
            "C4": CRITERIA_LABELS["C4"],
        }

        self.result_panes = tk.PanedWindow(
            table_frame,
            orient=tk.HORIZONTAL,
            sashwidth=10,
            sashrelief=tk.FLAT,
            bg="#9AA3AF",
            bd=0,
        )
        result_panes = self.result_panes
        result_panes.pack(fill="both", expand=True)

        table_panel = ttk.LabelFrame(result_panes, text="Результаты", padding=6)
        table_area = ttk.Frame(table_panel)
        table_area.pack(fill="both", expand=True)
        self.chart_frame = ttk.LabelFrame(result_panes, text="График вклада критериев", padding=8)

        result_panes.add(table_panel, minsize=240, stretch="always")
        result_panes.add(self.chart_frame, minsize=240, stretch="always")

        self.table = ttk.Treeview(table_area, columns=columns, show="headings", height=20)

        column_widths = {
            "Rank": 55,
            "TNVED": 80,
            "Score": 85,
            "Import": 115,
            "Export": 105,
            "C1": 120,
            "C2": 120,
            "C3": 165,
            "C4": 175,
        }

        min_column_widths = {
            "Rank": 35,
            "TNVED": 45,
            "Score": 55,
            "Import": 65,
            "Export": 65,
            "C1": 60,
            "C2": 60,
            "C3": 75,
            "C4": 75,
        }

        self.table_columns = columns
        self.table_headings = headings
        self.table_min_column_widths = min_column_widths

        for column in columns:
            self.table.heading(
                column,
                text=headings[column],
                command=lambda selected_column=column: self.sort_table_by_column(selected_column),
            )
            self.table.column(
                column,
                width=column_widths[column],
                minwidth=min_column_widths[column],
                anchor="center",
                stretch=True,
            )

        scrollbar = ttk.Scrollbar(table_area, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)

        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.table.bind("<Double-1>", self.shrink_column_on_separator_double_click)

        self.components_chart_label = ttk.Label(
            self.chart_frame,
            text="График появится после расчета",
            anchor="center",
        )
        self.components_chart_label.pack(fill="both", expand=True)
        self.root.after(100, self.set_initial_result_pane_width)

    def set_initial_result_pane_width(self, attempt=0):
        if self.result_panes is None:
            return

        self.root.update_idletasks()
        total_width = self.result_panes.winfo_width()

        if total_width <= 1 and attempt < 10:
            self.root.after(100, lambda: self.set_initial_result_pane_width(attempt + 1))
            return

        if total_width > 1:
            self.result_panes.sash_place(0, int(total_width * 2 / 3), 0)

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

        if not self.file_path.get().strip() or not path.is_file():
            return

        try:
            raw_data = loader.load_excel_data(path)
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

    def reset_ahp_matrix(self):
        self.fill_default_ahp_matrix()
        self.ahp_preview.set("Можете предварительно рассчитать веса")
        self.status.set("Матрица AHP сброшена к значениям по умолчанию")

    def preview_ahp_weights(self):
        try:
            pairwise_matrix = self.get_pairwise_matrix()
            weights, ahp_info = model.calculate_ahp_weights(pairwise_matrix)

            if ahp_info["is_consistent"]:
                consistency_text = "матрица согласована"
            else:
                consistency_text = "матрица не согласована"

            self.ahp_preview.set(
                " | ".join(
                    [
                        f"C1: {weights['C1']:.4f}",
                        f"C2: {weights['C2']:.4f}",
                        f"C3: {weights['C3']:.4f}",
                        f"C4: {weights['C4']:.4f}",
                        f"CR: {ahp_info['consistency_ratio']:.4f} ({consistency_text})",
                    ]
                )
            )
            self.status.set("Веса AHP рассчитаны предварительно")
        except Exception as error:
            self.status.set("Ошибка расчета весов AHP")
            messagebox.showerror("Ошибка расчета весов AHP", str(error))

    def update_ahp_inverse_labels(self, event=None):
        for (row_index, column_index), label in self.ahp_inverse_labels.items():
            source_entry = self.ahp_entries[(column_index, row_index)]

            try:
                value = self.parse_comparison_value(source_entry.get())
                inverse_value = 1 / value
                label.config(text=self.format_inverse_matrix_value(value, inverse_value))
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
        expert_count = int(self.expert_count.get())
        expert_weights = []

        for expert_index in range(expert_count):
            weights = {}

            for criterion in model.CRITERIA:
                variable = self.manual_weight_vars[(expert_index, criterion)]
                weights[criterion] = self.parse_weight_value(variable.get())

            try:
                model.check_weights(weights)
            except ValueError as error:
                raise ValueError(f"Эксперт {expert_index + 1}: {error}") from error

            expert_weights.append(weights)

        averaged_weights = {}
        for criterion in model.CRITERIA:
            averaged_weights[criterion] = sum(
                weights[criterion] for weights in expert_weights
            ) / expert_count

        model.check_weights(averaged_weights)
        return averaged_weights

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

    def format_inverse_matrix_value(self, source_value, inverse_value):
        if source_value > 1 and abs(source_value - round(source_value)) < 0.000001:
            return f"1/{int(round(source_value))}"

        return self.format_matrix_value(inverse_value)

    def calculate(self):
        try:
            path = Path(self.file_path.get())
            calculation_year = int(self.year.get())
            clipping_mode = self.clipping_mode.get()
            weight_method = self.weight_method.get()

            if not self.file_path.get().strip() or not path.is_file():
                raise ValueError("\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 Excel-\u0444\u0430\u0439\u043b \u0434\u0430\u043d\u043d\u044b\u0445")

            self.status.set("Выполняется расчет...")
            self.root.update_idletasks()

            raw_data = loader.load_excel_data(path)
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

            self.sort_column = None
            self.sort_descending = True
            self.ahp_preview.set("Можете предварительно рассчитать веса")
            self.update_table()
            self.update_summary(calculation_year, clipping_mode)
            self.update_charts_preview()
        except Exception as error:
            self.status.set("Ошибка расчета")
            messagebox.showerror("Ошибка расчета", str(error))

    def update_table(self, data=None):
        for item in self.table.get_children():
            self.table.delete(item)

        if data is None:
            data = self.ranking

        self.update_table_headings()

        for _, row in data.iterrows():
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

    def sort_table_by_column(self, column):
        if self.ranking is None:
            return

        if self.sort_column == column:
            self.sort_descending = not self.sort_descending
        else:
            self.sort_column = column
            self.sort_descending = True

        sorted_data = self.ranking.sort_values(
            by=column,
            ascending=not self.sort_descending,
            kind="mergesort",
        )
        self.update_table(sorted_data)

    def update_table_headings(self):
        for column in self.table_columns:
            heading = self.table_headings[column]

            if column == self.sort_column:
                arrow = " ↓" if self.sort_descending else " ↑"
                heading = f"{heading}{arrow}"

            self.table.heading(
                column,
                text=heading,
                command=lambda selected_column=column: self.sort_table_by_column(selected_column),
            )

    def shrink_column_on_separator_double_click(self, event):
        if self.table.identify_region(event.x, event.y) != "separator":
            return None

        column = self.find_column_left_of_separator(event.x)

        if column is not None:
            self.shrink_column_to_minimum(column)

        return "break"

    def shrink_column_to_minimum(self, column):
        column_index = self.table_columns.index(column)

        for table_column in self.table_columns:
            current_width = int(self.table.column(table_column, "width"))
            self.table.column(table_column, width=current_width)

        for index, table_column in enumerate(self.table_columns):
            self.table.column(table_column, stretch=index > column_index)

        self.table.column(column, width=self.table_min_column_widths[column])

    def find_column_left_of_separator(self, x_position):
        boundary_position = 0

        for column in self.table_columns:
            boundary_position += int(self.table.column(column, "width"))

            if abs(x_position - boundary_position) <= 8:
                return column

        return None

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

        self.summary_parameters.set(
            f"\u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b: \u043a\u043b\u0438\u043f\u043f\u0438\u043d\u0433 {clipping_mode}, \u043c\u0435\u0442\u043e\u0434 \u0432\u0435\u0441\u043e\u0432 {weight_method}"
        )
        self.summary_weights.set(
            " | ".join(
                [
                    f"\u0412\u0435\u0441\u0430: C1 {weights['C1']:.4f}",
                    f"C2 {weights['C2']:.4f}",
                    f"C3 {weights['C3']:.4f}",
                    f"C4 {weights['C4']:.4f}",
                    consistency_summary,
                ]
            )
        )

    def update_charts_preview(self):
        output_path = charts.save_score_components_chart(
            self.ranking,
            self.ahp_info,
            output_path="outputs/charts/preview/preview_score_components.png",
            top_n=10,
            figsize=(5.2, 4.0),
            dpi=100,
        )

        self.chart_images["score_components"] = tk.PhotoImage(
            file=output_path
        )
        self.components_chart_label.config(
            image=self.chart_images["score_components"],
            text="",
        )
        self.root.after_idle(self.expand_chart_pane_to_fit_preview)

    def expand_chart_pane_to_fit_preview(self):
        if self.result_panes is None or "score_components" not in self.chart_images:
            return

        self.root.update_idletasks()
        total_width = self.result_panes.winfo_width()

        if total_width <= 1:
            return

        image_width = self.chart_images["score_components"].width()
        chart_padding = 48
        minimum_table_width = 240
        required_chart_width = image_width + chart_padding

        sash_x = max(minimum_table_width, total_width - required_chart_width)
        self.result_panes.sash_place(0, sash_x, 0)

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

    def save_charts(self):
        if self.ranking is None or self.ahp_info is None:
            messagebox.showwarning("Нет данных", "Сначала выполните расчет")
            return

        output_path = filedialog.asksaveasfilename(
            title="Сохранить график",
            initialdir="outputs",
            initialfile=f"score_components_{self.year.get()}.png",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")],
        )

        if not output_path:
            return

        try:
            saved_path = charts.save_score_components_chart(
                self.ranking,
                self.ahp_info,
                output_path,
                top_n=10,
            )

            self.status.set(f"График сохранен: {saved_path}")
            messagebox.showinfo(
                "График сохранен",
                f"Файл сохранен:\n{saved_path}",
            )
        except Exception as error:
            messagebox.showerror("Ошибка сохранения графика", str(error))


def run_app():
    root = tk.Tk()
    app = ImportSubstitutionApp(root)
    root.mainloop()
    return app
