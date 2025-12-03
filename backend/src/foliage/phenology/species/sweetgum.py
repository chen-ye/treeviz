"""Sweetgum (Liquidambar styraciflua) phenology model."""
from ..base import TreePhenologyModel

class Sweetgum(TreePhenologyModel):
    """
    Liquidambar styraciflua.
    Late leaf out.
    Late fall color.
    Highly variable vibrant mix (Red/Purple/Yellow).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (100, 90, 80)
        juvenile_green = (120, 160, 80)
        mature_green = (34, 139, 34)
        fall_red = (220, 20, 60)
        fall_purple = (75, 0, 130)
        fall_yellow = (240, 200, 50)
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
        # Very late fall color.
        fall_start_dl = 11.0 + (drought * 1.5)
        fall_peak_dl = 10.0
        fall_end_dl = 9.0

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return bare_brown

        # Determine peak color based on sun/stress
        # High Sun (UV) -> Red/Purple. Low Sun -> Yellow.
        uv = row['uv_stress_factor']
        if uv > 0.5:
            target_peak = fall_purple
        elif uv > 0.2:
            target_peak = fall_red
        else:
            target_peak = fall_yellow

        if day_length > fall_peak_dl:
            # Green -> Target
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, target_peak, progress)
        elif day_length > fall_end_dl:
            # Target -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(target_peak, bare_brown, progress)
        else:
            return bare_brown
