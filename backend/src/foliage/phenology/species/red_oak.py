"""Northern Red Oak (Quercus rubra) phenology model."""
from ..base import TreePhenologyModel

class NorthernRedOak(TreePhenologyModel):
    """
    Quercus rubra.
    Late leaf out.
    Russet/Red fall color.
    Marcescent (holds brown leaves well into winter).
    """
    def _resolve_daily_color(self, row) -> tuple[int, int, int]:
        # Phase 1: Palette
        structure_grey = (90, 80, 70)   # Winter bark/branches
        juvenile_pink = (180, 100, 100) # Unfurling leaves often reddish/pinkish
        mature_green = (50, 100, 40)    # Deep green
        russet_red = (165, 42, 42)      # Peak Fall
        dry_brown = (139, 69, 19)       # Marcescent leaves

        # --- Inputs ---
        gdd = row['accumulated_gdd']
        day_length = row['day_length']
        drought = row['drought_stress']
        is_freeze = row['recent_freeze']

        # --- Phase 3 & 4: Logic & Triggers ---

        # 1. Spring (GDD Driven)
        # Late spring: 250 start, 350 full
        # Urban/Elevation modifiers applied to threshold
        leaf_start = self.get_adjusted_threshold(250, 'gdd')
        leaf_end = self.get_adjusted_threshold(350, 'gdd')

        if gdd < leaf_start:
            return structure_grey

        if gdd < leaf_end:
            # Transition: Structure -> Juvenile -> Green
            # We split the window: First half is Structure->Juvenile, Second is Juvenile->Green
            mid = (leaf_start + leaf_end) / 2
            if gdd < mid:
                progress = self._calc_progress(gdd, leaf_start, mid)
                return self._interp_hsl(structure_grey, juvenile_pink, progress)
            else:
                progress = self._calc_progress(gdd, mid, leaf_end)
                return self._interp_hsl(juvenile_pink, mature_green, progress)

        # 2. Summer / Early Fall
        # Trigger Fall: Photoperiod (Day Length) + Drought
        # Oaks are late turners.
        # Base trigger: 11.0 hours day length.
        # Drought advances it (makes trigger happen at longer days): + (drought * 1.0)
        fall_start_dl = 11.5 + (drought * 1.5) # If severe drought, starts at 13h (summer)
        fall_peak_dl = 10.5
        fall_end_dl = 9.5

        # Invert logic: As DL drops, progress increases
        # We need to handle the case where it's NOT fall yet (DL > fall_start_dl)
        if day_length > fall_start_dl and not is_freeze:
            return mature_green

        # 3. Fall Progression
        # If frozen, accelerate to brown
        if is_freeze:
            return dry_brown

        if day_length > fall_peak_dl:
            # Green -> Russet
            progress = self._calc_progress(fall_start_dl - day_length, 0, fall_start_dl - fall_peak_dl)
            return self._interp_hsl(mature_green, russet_red, progress)
        elif day_length > fall_end_dl:
            # Russet -> Brown
            progress = self._calc_progress(fall_peak_dl - day_length, 0, fall_peak_dl - fall_end_dl)
            return self._interp_hsl(russet_red, dry_brown, progress)
        else:
            # Marcescence: Holds brown leaves
            return dry_brown
