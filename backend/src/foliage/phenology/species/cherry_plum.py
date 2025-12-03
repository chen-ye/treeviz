"""Cherry Plum (Prunus cerasifera) phenology model."""
from ..base import TreePhenologyModel

class CherryPlum(TreePhenologyModel):
    """
    Prunus cerasifera 'Nigra'.
    Early spring flowering (pink).
    Dark purple foliage (emerges bronze/red).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_dark = (80, 70, 70)
        bud_pink = (200, 150, 160)
        bloom_pink = (255, 192, 203)
        juvenile_red = (140, 60, 60)
        mature_purple = (80, 20, 40)
        fall_bronze = (100, 60, 40)
        bare = (70, 60, 60)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Very early bloom: Start ~70, Peak ~110, End ~150
        # Leaves start: ~130 (during bloom), Mature ~250
        bloom_start = self.get_adjusted_threshold(70, 'gdd')
        bloom_peak = self.get_adjusted_threshold(110, 'gdd')
        bloom_end = self.get_adjusted_threshold(150, 'gdd')

        leaf_start = self.get_adjusted_threshold(130, 'gdd')
        leaf_mature = self.get_adjusted_threshold(250, 'gdd')

        # Bloom
        if gdd < bloom_start:
            return structure_dark

        if gdd < bloom_end:
            if gdd < bloom_peak:
                progress = self._calc_progress(gdd, bloom_start, bloom_peak)
                return self._interp_hsl(bud_pink, bloom_pink, progress)
            else:
                progress = self._calc_progress(gdd, bloom_peak, bloom_end)
                return self._interp_hsl(bloom_pink, juvenile_red, progress)

        # Leaf Out
        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_red, mature_purple, progress)

        # 2. Summer -> Fall
        # Cherry Plums lose leaves somewhat early or fade.
        fall_start_dl = 11.8 + (drought * 1.0)
        fall_end_dl = 10.5

        if day_length > fall_start_dl and not is_freeze:
            return mature_purple

        # 3. Fall Progression
        if is_freeze:
            return bare

        if day_length > fall_end_dl:
            # Purple -> Bronze
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_end_dl)
            return self._interp_hsl(mature_purple, fall_bronze, progress)
        else:
            return bare
