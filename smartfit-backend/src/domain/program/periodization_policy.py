from uuid import UUID, uuid4
from src.domain.program.entities import ProgramPhase


class ProgramPeriodizationPolicy:
    def create_phases(
        self,
        program_id: UUID,
        duration_weeks: int,
        goal: str,
        training_level: str,
        training_style: str,
    ) -> list[ProgramPhase]:
        phases_definition = []

        # Define structure based on duration
        if duration_weeks == 4:
            phases_definition = [
                ("foundation", 1, 1),
                ("accumulation", 2, 3),
                ("deload", 4, 4),
            ]
        elif duration_weeks == 6:
            phases_definition = [
                ("foundation", 1, 1),
                ("accumulation", 2, 4),
                ("intensification", 5, 5),
                ("deload", 6, 6),
            ]
        elif duration_weeks == 8:
            phases_definition = [
                ("foundation", 1, 2),
                ("accumulation", 3, 5),
                ("intensification", 6, 7),
                ("deload", 8, 8),
            ]
        elif duration_weeks == 12:
            phases_definition = [
                ("foundation", 1, 3),
                ("accumulation", 4, 7),
                ("intensification", 8, 10),
                ("deload", 11, 11),
                ("consolidation", 12, 12),
            ]
        else:
            # Fallback/default logic for arbitrary durations
            if duration_weeks < 4:
                phases_definition = [("foundation", 1, duration_weeks)]
            else:
                f_end = max(1, duration_weeks // 4)
                d_start = duration_weeks
                phases_definition = [
                    ("foundation", 1, f_end),
                    ("accumulation", f_end + 1, d_start - 1),
                    ("deload", d_start, duration_weeks),
                ]

        phases = []
        for phase_type, start, end in phases_definition:
            name = phase_type.capitalize() + " Phase"
            
            # Modifier defaults
            volume_mult = 1.0
            intensity_mult = 1.0
            rpe_mod = 0
            is_del = False
            
            if phase_type == "foundation":
                volume_mult = 0.85
                intensity_mult = 0.9
                rpe_mod = -1
                is_del = False
            elif phase_type == "accumulation":
                volume_mult = 1.0  # Range: 1.0 to 1.15
                intensity_mult = 1.0
                rpe_mod = 0
                is_del = False
            elif phase_type == "intensification":
                volume_mult = 0.9
                intensity_mult = 1.1
                rpe_mod = 1
                is_del = False
            elif phase_type == "deload":
                volume_mult = 0.6  # Range: 0.5 to 0.7
                intensity_mult = 0.85
                rpe_mod = -2
                is_del = True
            elif phase_type == "consolidation":
                volume_mult = 0.8
                intensity_mult = 1.0
                rpe_mod = 0
                is_del = False

            phases.append(
                ProgramPhase(
                    id=uuid4(),
                    program_id=program_id,
                    name=name,
                    phase_type=phase_type,
                    start_week=start,
                    end_week=end,
                    volume_multiplier=volume_mult,
                    intensity_multiplier=intensity_mult,
                    rpe_modifier=rpe_mod,
                    is_deload=is_del,
                    notes=f"Auto-generated {phase_type} phase",
                )
            )
        return phases
