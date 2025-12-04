"""European Hornbeam (Carpinus betulus) phenology model."""
from ..base import TreePhenologyModel

class EuropeanHornbeam(TreePhenologyModel):
    """
    Carpinus betulus.
    Dense green foliage.
    Yellow/Brown fall color.
    Marcescent (holds leaves).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (90, 80, 70)
        juvenile_green = (120, 180, 100) # Fresh green
        mature_green = (34, 139, 34)
        fall_yellow = (210, 180, 50)
        marcescent_brown = (160, 100, 60)

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Logic ---

        # 1. Spring (GDD)
        # Medium spring: ~150 start, ~250 mature
        leaf_start = self.get_adjusted_threshold(150, 'gdd')
        leaf_mature = self.get_adjusted_threshold(250, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        if gdd < leaf_mature:
            progress = self._calc_progress(gdd, leaf_start, leaf_mature)
            return self._interp_hsl(juvenile_green, mature_green, progress)

        # 2. Summer -> Fall
        # Turns medium-late
        fall_start_dl = 11.5 + (drought * 1.2)
        fall_peak_dl = 10.5
        fall_end_dl = 9.5

        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        if is_freeze:
            return marcescent_brown

        if day_length > fall_peak_dl:
            # Green -> Yellow
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, fall_yellow, progress)
        elif day_length > fall_end_dl:
            # Yellow -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(fall_yellow, marcescent_brown, progress)
        else:
            # Holds brown leaves
            return marcescent_brown
