from src.config.config import Config


class SizeRecommender:
    def __init__(self):
        self.size_rules = getattr(Config, "SIZE_RULES", {})
        self.size_order = getattr(Config, "SIZE_ORDER", list(self.size_rules.keys()))
        self.fit_offsets = getattr(
            Config,
            "SIZE_FIT_OFFSETS",
            {
                "slim_fit": -1,
                "regular_fit": 0,
                "loose_fit": 1,
            },
        )

    def _safe_get(self, measurements, key):
        aliases = {
            "shoulder_width": ["shoulder_width", "shoulder"],
            "shoulder": ["shoulder", "shoulder_width"],
        }

        for candidate_key in aliases.get(key, [key]):
            value = measurements.get(candidate_key)
            if value is None:
                continue

            try:
                return float(value)
            except (TypeError, ValueError):
                continue

        return None

    def _score_size(self, size_name, measurements):
        rule = self.size_rules.get(size_name, {})
        if not rule:
            return float("inf")

        total_score = 0.0
        matched = 0

        for key, value_range in rule.items():
            value = self._safe_get(measurements, key)
            if value is None:
                continue

            min_value, max_value = value_range
            center = (min_value + max_value) / 2.0
            half_span = max((max_value - min_value) / 2.0, 1.0)

            if min_value <= value <= max_value:
                distance = abs(value - center) / half_span
            elif value < min_value:
                distance = (min_value - value) / half_span + 1.0
            else:
                distance = (value - max_value) / half_span + 1.0

            total_score += distance
            matched += 1

        if matched == 0:
            return float("inf")

        return total_score / matched

    def _get_best_base_size(self, measurements):
        if not self.size_order:
            return "M"

        scored_sizes = []
        for size_name in self.size_order:
            score = self._score_size(size_name, measurements)
            scored_sizes.append((size_name, score))

        scored_sizes.sort(key=lambda item: item[1])

        if scored_sizes and scored_sizes[0][1] != float("inf"):
            return scored_sizes[0][0]

        return "M"

    def _shift_size(self, base_size, offset):
        if base_size not in self.size_order:
            return base_size

        index = self.size_order.index(base_size)
        new_index = min(max(index + offset, 0), len(self.size_order) - 1)
        return self.size_order[new_index]

    def _build_result(self, primary_size, measurements):
        result = {
            "primary": primary_size,
            "regular_fit": self._shift_size(primary_size, self.fit_offsets.get("regular_fit", 0)),
            "slim_fit": self._shift_size(primary_size, self.fit_offsets.get("slim_fit", -1)),
            "loose_fit": self._shift_size(primary_size, self.fit_offsets.get("loose_fit", 1)),
            "by_fit": {},
            "reference_measurements": {},
        }

        result["by_fit"] = {
            "slim_fit": result["slim_fit"],
            "regular_fit": result["regular_fit"],
            "loose_fit": result["loose_fit"],
        }

        for key in ["height", "shoulder_width", "chest", "waist", "hip"]:
            value = self._safe_get(measurements, key)
            if value is not None:
                result["reference_measurements"][key] = round(value, 1)

        return result

    def recommend(self, measurements):
        measurements = measurements or {}
        primary_size = self._get_best_base_size(measurements)
        return self._build_result(primary_size, measurements)

    def recommend_primary_size(self, measurements):
        return self.recommend(measurements).get("primary", "M")
    
    def get_size_format(self, measurements):
        """
        获取格式化后的尺码推荐字符串
        格式：L（宽松版）/ XL（修身版）
        """
        result = self.recommend(measurements)
        loose_size = result.get("loose_fit", "M")
        slim_size = result.get("slim_fit", "M")
        return f"{loose_size}（宽松版）/ {slim_size}（修身版）"
