"""Japanese Flowering Cherry (Prunus serrulata) phenology model."""
from ..base import TreePhenologyModel

class JapaneseFloweringCherry(TreePhenologyModel):
    """
    Prunus serrulata.
    Famous spring bloom (pink/white).
    Orange/Bronze fall color.
    Early leaf drop.
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_reddish = (100, 80, 80) # Cherry bark often reddish/shiny
        bud_swell = (180, 120, 120)       # Buds
        bloom_pink = (255, 190, 210)      # Peak bloom
        juvenile_bronze = (160, 120, 60)  # New leaves often bronze
        mature_green = (50, 100, 40)
        fall_orange = (235, 140, 50)
        fall_bronze = (205, 127, 50)
        bare_brown = (101, 67, 33) # Ground/Branches

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Phase 3 & 4: Logic & Triggers ---

        # 1. Spring (GDD Driven)
        # Bloom: Starts early ~120, Peaks ~160, Ends ~200
        # Leaves: Start ~180, Mature ~300
        bloom_start = self.get_adjusted_threshold(120, 'gdd')
        bloom_peak = self.get_adjusted_threshold(160, 'gdd')
        bloom_end = self.get_adjusted_threshold(200, 'gdd')

        leaf_start = self.get_adjusted_threshold(180, 'gdd')
        leaf_mature = self.get_adjusted_threshold(300, 'gdd')

        # Bloom Sequence
        if gdd < bloom_start:
            # Winter -> Bud Swell
            if gdd > bloom_start - 30:
                progress = self._calc_progress(gdd, bloom_start - 30, bloom_start)
                return self._interp_hsl(structure_reddish, bud_swell, progress)
            return structure_reddish

        if gdd < bloom_end:
            # Bloom -> Peak -> Fade
            if gdd < bloom_peak:
                progress = self._calc_progress(gdd, bloom_start, bloom_peak)
                return self._interp_hsl(bud_swell, bloom_pink, progress)
            else:
                progress = self._calc_progress(gdd, bloom_peak, bloom_end)
                # Fading bloom might mix with emerging leaves (green/bronze)
                # But here we fade to juvenile leaf color
                return self._interp_hsl(bloom_pink, juvenile_bronze, progress)

        # Leaf Out
        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature) # Overlaps with bloom end
            # Transition from Juvenile Bronze to Mature Green
            return self._interp_hsl(juvenile_bronze, mature_green, progress)

        # 2. Summer / Fall
        # Cherries turn somewhat early.
        fall_start_dl = 12.0 + (drought * 1.0)
        fall_peak_dl = 11.0
        fall_end_dl = 10.0

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            # Drop leaves -> Structure
            return structure_reddish

        if day_length > fall_peak_dl:
            # Green -> Orange
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_orange, progress)
        elif day_length > fall_end_dl:
            # Orange -> Bronze -> Drop
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_orange, fall_bronze, progress)
        else:
            # Bare
            return structure_reddish
