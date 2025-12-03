"""Callery Pear (Pyrus calleryana) phenology model."""
from ..base import TreePhenologyModel

class CalleryPear(TreePhenologyModel):
    """
    Pyrus calleryana.
    Early white bloom (very distinct).
    Glossy green leaves.
    Late purple/red fall color (often holds leaves very late).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (90, 80, 80)
        bud_white = (240, 240, 230)
        bloom_white = (255, 255, 255)
        juvenile_green = (100, 160, 100)
        mature_green = (34, 139, 34)
        fall_purple = (128, 40, 60)
        fall_red = (160, 20, 40)
        brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Very early bloom: Start ~80, Peak ~130, End ~180
        # Leaves start: ~160, Mature ~280
        bloom_start = self.get_adjusted_threshold(80, 'gdd')
        bloom_peak = self.get_adjusted_threshold(130, 'gdd')
        bloom_end = self.get_adjusted_threshold(180, 'gdd')

        leaf_start = self.get_adjusted_threshold(160, 'gdd')
        leaf_mature = self.get_adjusted_threshold(280, 'gdd')

        # Bloom
        if gdd < bloom_start:
            return structure_grey

        if gdd < bloom_end:
            if gdd < bloom_peak:
                progress = self._calc_progress(gdd, bloom_start, bloom_peak)
                return self._interp_hsl(bud_white, bloom_white, progress)
            else:
                progress = self._calc_progress(gdd, bloom_peak, bloom_end)
                return self._interp_hsl(bloom_white, juvenile_green, progress)

        # Leaf Out
        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Pears turn late.
        fall_start_dl = 11.0 + (drought * 1.5)
        fall_peak_dl = 10.0
        fall_end_dl = 9.0

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return brown # Late hard freeze kills leaves

        if day_length > fall_peak_dl:
            # Green -> Purple
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_purple, progress)
        elif day_length > fall_end_dl:
            # Purple -> Red -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_purple, fall_red, progress)
        else:
            return brown
