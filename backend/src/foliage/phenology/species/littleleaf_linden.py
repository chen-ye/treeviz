"""Littleleaf Linden (Tilia cordata) phenology model."""
from ..base import TreePhenologyModel

class LittleleafLinden(TreePhenologyModel):
    """
    Tilia cordata.
    Heart-shaped leaves.
    Yellow fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (90, 80, 70)
        juvenile_lime = (160, 220, 100)
        mature_green = (34, 139, 34)
        fall_yellow = (240, 230, 140)
        bare_brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Mid spring: ~160 start, ~260 mature
        leaf_start = self.get_adjusted_threshold(160, 'gdd')
        leaf_mature = self.get_adjusted_threshold(260, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_lime, mature_green, progress)

        # 2. Summer -> Fall
        # Mid-Late fall.
        fall_start_dl = 11.2 + (drought * 1.2)
        fall_peak_dl = 10.2
        fall_end_dl = 9.2

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
            # Yellow -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_yellow, bare_brown, progress)
        else:
            return bare_brown
