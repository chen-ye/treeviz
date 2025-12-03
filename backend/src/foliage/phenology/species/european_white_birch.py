"""European White Birch (Betula pendula) phenology model."""
from ..base import TreePhenologyModel

class EuropeanWhiteBirch(TreePhenologyModel):
    """
    Betula pendula.
    White bark (visible in winter).
    Bright yellow fall color.
    Drops leaves early.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_white = (200, 200, 190) # White bark
        juvenile_green = (150, 220, 100)
        mature_green = (100, 180, 80)
        fall_yellow = (240, 220, 20)
        bare_brown = (130, 100, 80) # Branches

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Early spring: ~100 start, ~200 mature
        leaf_start = self.get_adjusted_threshold(100, 'gdd')
        leaf_mature = self.get_adjusted_threshold(200, 'gdd')

        if gdd < leaf_start:
            return structure_white

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Early fall, especially if dry
        fall_start_dl = 12.5 + (drought * 2.0) # Sensitive to drought
        fall_peak_dl = 11.5
        fall_end_dl = 10.5

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return structure_white

        if day_length > fall_peak_dl:
            # Green -> Yellow
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_yellow, progress)
        elif day_length > fall_end_dl:
            # Yellow -> Bare (Structure)
            # Birches drop quickly
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_yellow, structure_white, progress)
        else:
            return structure_white
