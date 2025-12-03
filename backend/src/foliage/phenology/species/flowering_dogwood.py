"""Flowering Dogwood (Cornus florida) phenology model."""
from ..base import TreePhenologyModel

class FloweringDogwood(TreePhenologyModel):
    """
    Cornus florida.
    Spring white/pink bracts.
    Red fall color.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (100, 90, 90)
        bud_swell = (180, 180, 170)
        bloom_white = (255, 250, 240)
        juvenile_green = (100, 160, 100)
        mature_green = (60, 100, 60)
        fall_red = (178, 34, 34)
        fall_maroon = (100, 20, 20)
        bare_brown = (101, 67, 33)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Early-Mid spring bloom: ~120 start, ~180 peak, ~250 end
        # Leaves follow bloom
        bloom_start = self.get_adjusted_threshold(120, 'gdd')
        bloom_peak = self.get_adjusted_threshold(180, 'gdd')
        bloom_end = self.get_adjusted_threshold(250, 'gdd')

        leaf_start = self.get_adjusted_threshold(220, 'gdd')
        leaf_mature = self.get_adjusted_threshold(350, 'gdd')

        # Bloom
        if gdd < bloom_start:
            return structure_grey

        if gdd < bloom_end:
            if gdd < bloom_peak:
                progress = self._calc_progress(gdd, bloom_start, bloom_peak)
                return self._interp_hsl(bud_swell, bloom_white, progress)
            else:
                progress = self._calc_progress(gdd, bloom_peak, bloom_end)
                return self._interp_hsl(bloom_white, juvenile_green, progress)

        # Leaf Out
        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Turns medium time.
        fall_start_dl = 11.2 + (drought * 1.5)
        fall_peak_dl = 10.2
        fall_end_dl = 9.2

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return bare_brown

        if day_length > fall_peak_dl:
            # Green -> Red
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_red, progress)
        elif day_length > fall_end_dl:
            # Red -> Maroon -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_red, fall_maroon, progress)
        else:
            return bare_brown
