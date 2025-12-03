"""Honeylocust (Gleditsia triacanthos) phenology model."""
from ..base import TreePhenologyModel

class Honeylocust(TreePhenologyModel):
    """
    Gleditsia triacanthos.
    Late leaf out.
    Clear yellow fall color.
    Drops leaves early.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_dark = (60, 50, 40)
        juvenile_green = (140, 180, 60) # Light fern green
        mature_green = (85, 107, 47)    # Olive green
        fall_yellow = (255, 215, 0)
        bare_brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Late leaf out: ~220 start, ~350 mature
        leaf_start = self.get_adjusted_threshold(220, 'gdd')
        leaf_mature = self.get_adjusted_threshold(350, 'gdd')

        if gdd < leaf_start:
            return structure_dark

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Early fall turn.
        fall_start_dl = 12.0 + (drought * 1.5)
        fall_peak_dl = 11.0
        fall_end_dl = 10.0

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return structure_dark

        if day_length > fall_peak_dl:
            # Green -> Yellow
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_yellow, progress)
        elif day_length > fall_end_dl:
            # Yellow -> Bare
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_yellow, structure_dark, progress)
        else:
            return structure_dark
