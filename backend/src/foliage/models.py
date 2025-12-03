from abc import ABC, abstractmethod
import math

class PhenologyModel(ABC):
    @abstractmethod
    def get_color(self, doy: int, weather_factor: float = 1.0) -> tuple[int, int, int]:
        """Returns RGB color for a given Day of Year."""
        pass

    def generate_timeline(self, days=365) -> list[tuple[int, int, int]]:
        return [self.get_color(d) for d in range(1, days + 1)]

class DeciduousModel(PhenologyModel):
    def __init__(self,
                 summer_color=(34, 139, 34),
                 peak_color=(255, 165, 0),
                 winter_color=(139, 69, 19),
                 fall_start=280,
                 fall_peak=305,
                 fall_end=330):
        self.summer = summer_color
        self.peak = peak_color
        self.winter = winter_color
        self.start = fall_start
        self.peak_doy = fall_peak
        self.end = fall_end

    def get_color(self, doy: int, weather_factor: float = 1.0) -> tuple[int, int, int]:
        # Simple Logic (same as before but modular)
        # Weather shift
        shift = (weather_factor - 1.0) * 10
        d = doy + shift

        if d < self.start:
            return self.summer
        elif d > self.end:
            return self.winter

        if d < self.peak_doy:
            t = (d - self.start) / (self.peak_doy - self.start)
            return self._interp(self.summer, self.peak, t)
        else:
            t = (d - self.peak_doy) / (self.end - self.peak_doy)
            return self._interp(self.peak, self.winter, t)

    def _interp(self, c1, c2, t):
        return (
            int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t)
        )

class FloweringModel(DeciduousModel):
    def __init__(self,
                 flower_color=(255, 192, 203), # Pink
                 flower_start=80,
                 flower_end=100,
                 **kwargs):
        super().__init__(**kwargs)
        self.flower = flower_color
        self.f_start = flower_start
        self.f_end = flower_end

    def get_color(self, doy: int, weather_factor: float = 1.0) -> tuple[int, int, int]:
        # Check flowering window first
        if self.f_start <= doy <= self.f_end:
            # Fade in/out could be added
            return self.flower

        return super().get_color(doy, weather_factor)
