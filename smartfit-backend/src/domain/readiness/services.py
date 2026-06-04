from src.domain.common.enums import ReadinessCategory, ReadinessRecommendation
from src.domain.health.entities import HealthSummary, ManualCheckin


class ReadinessCalculator:
    def calculate(
        self,
        *,
        health_summary: HealthSummary | None,
        manual_checkin: ManualCheckin | None,
        hrv_baseline: float | None = None,
        rhr_baseline: float | None = None,
        recent_load_score: float = 75.0,
    ) -> tuple[float, ReadinessCategory, ReadinessRecommendation, float, str]:
        sleep = self._sleep_score(health_summary)
        hrv = self._hrv_score(health_summary, hrv_baseline)
        rhr = self._rhr_score(health_summary, rhr_baseline)
        self_report = self._self_report_score(manual_checkin)
        load = self._recent_load_score(recent_load_score)

        score = round(
            self._weighted_score(
                health_summary=health_summary,
                manual_checkin=manual_checkin,
                sleep=sleep,
                hrv=hrv,
                rhr=rhr,
                self_report=self_report,
                load=load,
            ),
            2,
        )
        category = self._category(score)
        recommendation = self._recommendation(score)
        confidence = self._confidence_level(
            health_summary, manual_checkin, hrv_baseline, rhr_baseline
        )
        explanation = self._build_explanation(
            score, category, sleep, hrv, rhr, self_report, load
        )
        return score, category, recommendation, confidence, explanation

    def _sleep_score(self, health_summary: HealthSummary | None) -> float:
        if health_summary is None or health_summary.sleep_hours is None:
            return 50.0
        hours = health_summary.sleep_hours
        if hours >= 8:
            return 95.0
        if hours >= 7:
            return 85.0
        if hours >= 6:
            return 70.0
        if hours >= 5:
            return 50.0
        return 30.0

    def _hrv_score(
        self, health_summary: HealthSummary | None, hrv_baseline: float | None
    ) -> float:
        if health_summary is None or health_summary.heart_rate_variability is None:
            return 50.0
        hrv = health_summary.heart_rate_variability
        if hrv_baseline is not None and hrv_baseline > 0:
            ratio = hrv / hrv_baseline
            if ratio >= 1.1:
                return 95.0
            if ratio >= 1.0:
                return 85.0
            if ratio >= 0.9:
                return 70.0
            if ratio >= 0.8:
                return 50.0
            return 25.0
        if hrv >= 80:
            return 95.0
        if hrv >= 60:
            return 85.0
        if hrv >= 45:
            return 70.0
        if hrv >= 30:
            return 50.0
        return 25.0

    def _rhr_score(
        self, health_summary: HealthSummary | None, rhr_baseline: float | None
    ) -> float:
        if health_summary is None or health_summary.resting_heart_rate is None:
            return 50.0
        rhr = health_summary.resting_heart_rate
        if rhr_baseline is not None and rhr_baseline > 0:
            delta = rhr - rhr_baseline
            if delta <= -3:
                return 95.0
            if delta <= 0:
                return 85.0
            if delta <= 4:
                return 70.0
            if delta <= 8:
                return 50.0
            return 25.0
        if rhr <= 55:
            return 95.0
        if rhr <= 62:
            return 85.0
        if rhr <= 70:
            return 70.0
        if rhr <= 78:
            return 50.0
        return 25.0

    def _self_report_score(self, manual_checkin: ManualCheckin | None) -> float:
        if manual_checkin is None:
            return 50.0
        normalized = (
            manual_checkin.energy
            + manual_checkin.motivation
            + manual_checkin.sleep_quality
            + (6 - manual_checkin.soreness)
            + (6 - manual_checkin.stress)
        )
        return round((normalized / 25) * 100, 2)

    def _recent_load_score(self, recent_load_score: float) -> float:
        return max(0.0, min(100.0, recent_load_score))

    def _weighted_score(
        self,
        *,
        health_summary: HealthSummary | None,
        manual_checkin: ManualCheckin | None,
        sleep: float,
        hrv: float,
        rhr: float,
        self_report: float,
        load: float,
    ) -> float:
        health_available = any(
            (
                health_summary and health_summary.sleep_hours is not None,
                health_summary and health_summary.heart_rate_variability is not None,
                health_summary and health_summary.resting_heart_rate is not None,
            )
        )
        load_weight = 0.25 if health_available else 0.55
        manual_weight = 0.25 if health_available else 0.45
        components: list[tuple[float, float]] = [(load, load_weight)]
        if health_summary and health_summary.sleep_hours is not None:
            components.append((sleep, 0.2))
        if health_summary and health_summary.heart_rate_variability is not None:
            components.append((hrv, 0.15))
        if health_summary and health_summary.resting_heart_rate is not None:
            components.append((rhr, 0.1))
        if manual_checkin is not None:
            components.append((self_report, manual_weight))
        if len(components) == 1:
            return load
        total_weight = sum(weight for _, weight in components)
        return sum(value * weight for value, weight in components) / total_weight

    def _category(self, score: float) -> ReadinessCategory:
        if score >= 85:
            return ReadinessCategory.EXCELLENT
        if score >= 70:
            return ReadinessCategory.GOOD
        if score >= 50:
            return ReadinessCategory.MODERATE
        if score >= 30:
            return ReadinessCategory.LOW
        return ReadinessCategory.VERY_LOW

    def _recommendation(self, score: float) -> ReadinessRecommendation:
        if score >= 85:
            return ReadinessRecommendation.TRAIN_HARD
        if score >= 65:
            return ReadinessRecommendation.TRAIN_NORMAL
        if score >= 45:
            return ReadinessRecommendation.REDUCE_VOLUME
        if score >= 20:
            return ReadinessRecommendation.RECOVERY
        return ReadinessRecommendation.REST

    def _confidence_level(
        self,
        health_summary: HealthSummary | None,
        manual_checkin: ManualCheckin | None,
        hrv_baseline: float | None,
        rhr_baseline: float | None,
    ) -> float:
        confidence = 0.4
        if health_summary and health_summary.sleep_hours is not None:
            confidence += 0.25
        if health_summary and health_summary.heart_rate_variability is not None:
            confidence += 0.2 if hrv_baseline is not None else 0.17
        if health_summary and health_summary.resting_heart_rate is not None:
            confidence += 0.15 if rhr_baseline is not None else 0.13
        if manual_checkin:
            confidence += 0.15
        return round(min(confidence, 1.0), 2)

    def _build_explanation(
        self,
        score: float,
        category: ReadinessCategory,
        sleep_score: float,
        hrv_score: float,
        rhr_score: float,
        self_report_score: float,
        load_score: float,
    ) -> str:
        return (
            f"Readiness {score:.0f}/100 ({category.value}). "
            f"Sleep={sleep_score:.0f}, HRV={hrv_score:.0f}, RHR={rhr_score:.0f}, "
            f"self-report={self_report_score:.0f}, load={load_score:.0f}."
        )
