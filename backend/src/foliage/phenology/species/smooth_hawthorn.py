"""Smooth Hawthorn (Crataegus laevigata) phenology model."""
from ..base import TreePhenologyModel

class SmoothHawthorn(TreePhenologyModel):
    """
    Crataegus laevigata.
    Late spring white flowers.
    Red berries in fall.
    Yellow/Orange fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (100, 90, 80)
        bud_green = (140, 160, 100)
        bloom_white = (250, 250, 240)
        mature_green = (60, 120, 50)
        fall_yellow = (220, 180, 60)
        fall_orange = (200, 100, 40)
        bare_brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Leaves start ~150.
        # Bloom Late Spring: ~250 start, ~350 end.
        leaf_start = self.get_adjusted_threshold(150, 'gdd')
        bloom_start = self.get_adjusted_threshold(250, 'gdd')
        bloom_peak = self.get_adjusted_threshold(300, 'gdd')
        bloom_end = self.get_adjusted_threshold(350, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        # Leaf out before bloom
        if gdd < bloom_start:
            progress = self._calc_progress(gdd, leaf_start, bloom_start)
            return self._interp_hsl(bud_green, mature_green, progress)

        # Bloom on top of green
        if gdd < bloom_end:
            # We simulate "white flowers on green" by blending towards white
            if gdd < bloom_peak:
                progress = self._calc_progress(gdd, bloom_start, bloom_peak)
                return self._interp_hsl(mature_green, bloom_white, progress)
            else:
                progress = self._calc_progress(gdd, bloom_peak, bloom_end)
                return self._interp_hsl(bloom_white, mature_green, progress)

        # 2. Summer -> Fall
        fall_start_dl = 11.5 + (drought * 1.0)
        fall_peak_dl = 10.5
        fall_end_dl = 9.5

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
            # Yellow -> Orange -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_yellow, fall_orange, progress)
        else:
            return bare_brown
