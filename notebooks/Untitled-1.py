class TableResponseProcessor:
    """
    Builds compact, chart-oriented table summaries for a Plotly presenter LLM.
    The LLM receives metadata and limited column examples, but never the full data.
    """

    def __init__(
        self,
        max_examples: int = 3,
        low_cardinality_threshold: int = 10,
        medium_cardinality_threshold: int = 50,
        categorical_numeric_threshold: int = 12,
    ):
        self.max_examples = max_examples
        self.low_cardinality_threshold = low_cardinality_threshold
        self.medium_cardinality_threshold = medium_cardinality_threshold
        self.categorical_numeric_threshold = categorical_numeric_threshold

    def process(
        self,
        items: Iterable[tuple["TableCard", pd.DataFrame]],
    ) -> str:
        """
        Process multiple (TableCard, DataFrame) pairs into one text block
        for the presenter prompt.
        """

        blocks: list[str] = []

        for table_card, df in items:
            blocks.append(self.process_table(df=df, table_card=table_card))

        #return "\n\n" + ("=" * 80) + "\n\n".join(blocks)
        return ("\n\n" + "=" * 80 + "\n\n").join(blocks)

    def process_table(
        self,
        df: pd.DataFrame,
        table_card: "TableCard",
    ) -> str:
        """
        Convert one DataFrame + TableCard into compact, LLM-friendly text.
        """

        table_name = getattr(table_card, "name", "unknown_table")
        table_description = getattr(table_card, "description", None)

        lines: list[str] = []

        lines.append(f"Table: {table_name}")

        if table_description:
            lines.append(f"Description: {table_description}")

        lines.append(f"Rows: {len(df)}")
        lines.append(f"Columns: {len(df.columns)}")

        lines.append("")
        lines.append("Column summaries:")

        for col in df.columns:
            summary = self.infer_column_summary(df[col])

            description = self.get_column_description(table_card, col)
            if description:
                summary["description"] = description

            lines.append(f"- Column: {col}")

            preferred_order = [
                "description",
                "dtype",
                "role",
                "unique_count",
                "unique_ratio",
                "cardinality",
                "null_count",
                "null_ratio",
                "min",
                "max",
                "mean",
                "median",
                "min_date",
                "max_date",
                "common_interval",
                "is_monotonic_increasing",
                "has_negative_values",
                "has_zero_values",
                "example_values",
            ]

            for key in preferred_order:
                if key in summary:
                    lines.append(f"  {key}: {summary[key]}")

        return "\n".join(lines)

    def infer_column_role(self, s: pd.Series) -> str:
        """
        Infer a chart-oriented semantic role.
        """

        if pd.api.types.is_datetime64_any_dtype(s):
            return "temporal"

        if pd.api.types.is_bool_dtype(s):
            return "categorical"

        if pd.api.types.is_numeric_dtype(s):
            nunique = s.nunique(dropna=True)

            if nunique <= self.categorical_numeric_threshold:
                return "categorical_numeric"

            return "quantitative"

        if pd.api.types.is_string_dtype(s) or pd.api.types.is_object_dtype(s):
            parsed = pd.to_datetime(s.dropna(), errors="coerce")
            valid_ratio = parsed.notna().mean() if len(parsed) else 0.0

            if valid_ratio >= 0.9:
                return "temporal"

            return "categorical"

        return "unknown"

    def infer_column_summary(self, s: pd.Series) -> dict[str, Any]:
        """
        Produce compact metadata for one DataFrame column.
        """

        non_null = s.dropna()

        row_count = len(s)
        non_null_count = len(non_null)
        null_count = row_count - non_null_count
        null_ratio = null_count / row_count if row_count else 0.0

        unique_count = non_null.nunique(dropna=True)
        unique_ratio = unique_count / row_count if row_count else 0.0

        role = self.infer_column_role(s)

        summary: dict[str, Any] = {
            "dtype": str(s.dtype),
            "role": role,
            "non_null_count": int(non_null_count),
            "null_count": int(null_count),
            "null_ratio": round(null_ratio, 4),
            "unique_count": int(unique_count),
            "unique_ratio": round(unique_ratio, 4),
        }

        if role in {"categorical", "categorical_numeric"}:
            summary["cardinality"] = self.classify_cardinality(unique_count)

            examples = (
                non_null
                .drop_duplicates()
                .astype(str)
                .head(self.max_examples)
                .tolist()
            )

            if examples:
                summary["example_values"] = examples

        elif role == "quantitative":
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()

            if not numeric.empty:
                summary.update(
                    {
                        "min": round(float(numeric.min()), 4),
                        "max": round(float(numeric.max()), 4),
                        "mean": round(float(numeric.mean()), 4),
                        "median": round(float(numeric.median()), 4),
                        "has_negative_values": bool((numeric < 0).any()),
                        "has_zero_values": bool((numeric == 0).any()),
                    }
                )

        elif role == "temporal":
            dt = pd.to_datetime(non_null, errors="coerce").dropna()

            if not dt.empty:
                summary.update(
                    {
                        "min_date": str(dt.min()),
                        "max_date": str(dt.max()),
                        "is_monotonic_increasing": bool(dt.is_monotonic_increasing),
                    }
                )

                if len(dt) > 1:
                    diffs = dt.sort_values().diff().dropna()
                    if not diffs.empty:
                        mode_diff = diffs.mode()
                        if not mode_diff.empty:
                            summary["common_interval"] = str(mode_diff.iloc[0])

        return summary

    def classify_cardinality(self, unique_count: int) -> str:
        """
        Convert unique count into low/medium/high cardinality label.
        """

        if unique_count <= self.low_cardinality_threshold:
            return "low"

        if unique_count <= self.medium_cardinality_threshold:
            return "medium"

        return "high"

    def get_column_description(
        self,
        table_card: "TableCard",
        column_name: str,
    ) -> str | None:
        """
        Extract column description from a TableCard, if present.

        Supports columns represented as either objects or dictionaries.
        """

        columns = getattr(table_card, "columns", None)

        if not columns:
            return None

        for col in columns:
            if isinstance(col, dict):
                name = col.get("name")
                description = col.get("description")
            else:
                name = getattr(col, "name", None)
                description = getattr(col, "description", None)

            if name == column_name:
                return description

        return None
    
DataResult
