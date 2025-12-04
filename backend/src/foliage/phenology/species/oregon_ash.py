"""Oregon Ash (Fraxinus latifolia) phenology model."""
from ..base import TreePhenologyModel

class OregonAsh(TreePhenologyModel):
    """
    Fraxinus latifolia.
    Native.
    Yellow fall color.
    Late leaf out.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (110, 100, 90)
        juvenile_green = (140, 180, 80)
        mature_green = (85, 107, 47)
        fall_yellow = (255, 215, 0)
        bare_brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Late leaf out: ~250 start, ~350 mature
        leaf_start = self.get_adjusted_threshold(250, 'gdd')
        leaf_mature = self.get_adjusted_threshold(350, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Early fall color.
        fall_start_dl = 12.0 + (drought * 1.5)
        fall_peak_dl = 11.0
        fall_end_dl = 10.0

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return bare_brown

        if day_length > fall_peak_dl:
            # Green -> Yellow
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_yellow, progress)
        elif day_length > fall_end_dl:
            # Yellow -> Bare
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_yellow, bare_brown, progress)
        else:
            return bare_brown
