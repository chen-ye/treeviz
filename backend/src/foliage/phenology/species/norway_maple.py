"""Norway Maple (Acer platanoides) phenology model."""
from ..base import TreePhenologyModel

class NorwayMaple(TreePhenologyModel):
    """
    Acer platanoides.
    Standard green to yellow/gold fall color.
    Late leaf drop.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (110, 100, 90)
        juvenile_green = (160, 200, 100) # Bright green
        mature_green = (54, 124, 43)
        fall_gold = (240, 190, 40)
        fall_orange = (220, 140, 20)
        brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Mid spring leaf out: ~200 start, ~300 mature
        leaf_start = self.get_adjusted_threshold(200, 'gdd')
        leaf_mature = self.get_adjusted_threshold(300, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Turns relatively late.
        fall_start_dl = 11.0 + (drought * 1.5)
        fall_peak_dl = 10.0
        fall_end_dl = 9.0

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return brown

        # Determine peak color based on sun/stress
        # UV/Elevation can add orange tints
        target_peak = fall_gold
        if row['uv_stress_factor'] > 0.3:
            target_peak = self._interp_hsl(fall_gold, fall_orange, row['uv_stress_factor'])

        if day_length > fall_peak_dl:
            # Green -> Gold
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, target_peak, progress)
        elif day_length > fall_end_dl:
            # Gold -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(target_peak, brown, progress)
        else:
            return brown
