"""
Thanos Disintegration (Endgame) Particle & Dissolve Effect.
Original beloved aesthetic: Organic fractal noise, natural ash particles,
and subtle charred dissolving boundaries.
"""

import cv2
import numpy as np


class ThanosDisintegrationEngine:
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.is_active = False
        self.is_finished = False

        # State storage
        self.frozen_person = None
        self.frozen_mask = None
        self.background_plate = None

        # Dissolve parameters
        self.progress = 0.0
        self.duration_frames = int(2.4 * fps)  # 2.4 seconds dissolve
        self.current_frame = 0
        self.dissolve_map = None

        # Particle pool (vectorized NumPy arrays)
        self.max_particles = 30000
        self.pos = np.zeros((0, 2), dtype=np.float32)       # [x, y]
        self.vel = np.zeros((0, 2), dtype=np.float32)       # [vx, vy]
        self.colors = np.zeros((0, 3), dtype=np.float32)    # [B, G, R]
        self.life = np.zeros(0, dtype=np.float32)           # remaining life (1.0 -> 0.0)
        self.decay = np.zeros(0, dtype=np.float32)          # decay rate per frame
        self.sizes = np.zeros(0, dtype=np.float32)          # particle radius

    def _generate_dissolve_map(self) -> np.ndarray:
        """
        Creates an organic fractal noise map mixed with directional wind gradient
        similar to the original Avengers disintegration effect.
        """
        h, w = self.height, self.width

        # Low-frequency smooth noise (macro clumps)
        grid_h1, grid_w1 = max(4, h // 32), max(4, w // 32)
        noise1 = cv2.resize(
            np.random.rand(grid_h1, grid_w1).astype(np.float32),
            (w, h),
            interpolation=cv2.INTER_CUBIC,
        )

        # Mid-frequency noise (medium details)
        grid_h2, grid_w2 = max(8, h // 12), max(8, w // 12)
        noise2 = cv2.resize(
            np.random.rand(grid_h2, grid_w2).astype(np.float32),
            (w, h),
            interpolation=cv2.INTER_CUBIC,
        )

        # High-frequency noise (fine ash grain)
        grid_h3, grid_w3 = max(16, h // 4), max(16, w // 4)
        noise3 = cv2.resize(
            np.random.rand(grid_h3, grid_w3).astype(np.float32),
            (w, h),
            interpolation=cv2.INTER_CUBIC,
        )

        combined_noise = 0.5 * noise1 + 0.35 * noise2 + 0.15 * noise3

        # Directional gradient: dissolves from bottom-right towards top-left (blown by wind)
        y_grid, x_grid = np.mgrid[0:h, 0:w]
        gradient = (y_grid / h) * 0.35 + (1.0 - x_grid / w) * 0.35

        dissolve = combined_noise * 0.5 + gradient
        dissolve = (dissolve - dissolve.min()) / (dissolve.max() - dissolve.min() + 1e-6)
        return dissolve.astype(np.float32)

    def start(self, person_frame: np.ndarray, person_mask: np.ndarray, background_plate: np.ndarray, duration_sec: float = 2.4, wind_direction: str = "top_right"):
        """Freezes the user's current frame and starts the disintegration sequence."""
        self.frozen_person = person_frame.copy()
        mask = person_mask.copy().astype(np.float32)
        if len(mask.shape) == 3:
            mask = mask[:, :, 0]
        if mask.max() > 1.0:
            mask /= 255.0
        self.frozen_mask = mask

        self.background_plate = background_plate.copy()
        self.duration_frames = max(30, int(duration_sec * self.fps))
        self.current_frame = 0
        self.progress = 0.0
        self.is_active = True
        self.is_finished = False

        self.dissolve_map = self._generate_dissolve_map()

        # Reset particle arrays
        self.pos = np.zeros((0, 2), dtype=np.float32)
        self.vel = np.zeros((0, 2), dtype=np.float32)
        self.colors = np.zeros((0, 3), dtype=np.float32)
        self.life = np.zeros(0, dtype=np.float32)
        self.decay = np.zeros(0, dtype=np.float32)
        self.sizes = np.zeros(0, dtype=np.float32)

    def reset(self):
        """Restores live camera mode."""
        self.is_active = False
        self.is_finished = False
        self.current_frame = 0
        self.progress = 0.0
        self.pos = np.zeros((0, 2), dtype=np.float32)

    def update(self) -> np.ndarray:
        """Updates particle simulation and returns the composited frame."""
        if not self.is_active:
            return None

        prev_tau = self.progress
        self.current_frame += 1
        self.progress = min(1.0, self.current_frame / self.duration_frames)
        curr_tau = self.progress

        h, w = self.height, self.width

        # 1. Identify newly dissolved pixels in this frame
        newly_dissolved = (
            (self.dissolve_map >= prev_tau)
            & (self.dissolve_map < curr_tau)
            & (self.frozen_mask > 0.4)
        )

        ys, xs = np.nonzero(newly_dissolved)
        num_candidates = len(xs)

        # 2. Spawn particles from newly dissolved regions
        if num_candidates > 0 and len(self.pos) < self.max_particles:
            sample_rate = max(1, num_candidates // 1600)
            sampled_xs = xs[::sample_rate]
            sampled_ys = ys[::sample_rate]
            n_new = len(sampled_xs)

            if n_new > 0:
                new_pos = np.column_stack([sampled_xs, sampled_ys]).astype(np.float32)

                # Realistic Thanos ash physics:
                vx = np.random.uniform(2.0, 7.0, n_new).astype(np.float32)    # Wind drift
                vy = np.random.uniform(-5.0, -1.0, n_new).astype(np.float32)  # Upward float

                # Sampled person color blended with ash gray
                sampled_bgr = self.frozen_person[sampled_ys, sampled_xs].astype(np.float32)
                gray = np.mean(sampled_bgr, axis=1, keepdims=True)
                ash_bgr = (0.35 * sampled_bgr + 0.65 * gray) * 0.75

                new_colors = ash_bgr
                new_life = np.ones(n_new, dtype=np.float32)
                new_decay = np.random.uniform(0.015, 0.035, n_new).astype(np.float32)
                new_sizes = np.random.uniform(1.5, 3.2, n_new).astype(np.float32)

                self.pos = np.vstack([self.pos, new_pos])
                self.vel = np.vstack([self.vel, np.column_stack([vx, vy])])
                self.colors = np.vstack([self.colors, new_colors])
                self.life = np.concatenate([self.life, new_life])
                self.decay = np.concatenate([self.decay, new_decay])
                self.sizes = np.concatenate([self.sizes, new_sizes])

        # 3. Update existing particles (vectorized physics)
        if len(self.pos) > 0:
            flutter = np.random.uniform(-0.5, 0.5, self.pos.shape).astype(np.float32)
            self.pos += self.vel + flutter
            self.vel[:, 1] += np.random.uniform(-0.05, 0.02, len(self.pos))
            self.vel[:, 0] *= 0.99
            self.life -= self.decay
            self.sizes *= 0.985

            alive = (
                (self.life > 0.0)
                & (self.pos[:, 0] >= 0)
                & (self.pos[:, 0] < w)
                & (self.pos[:, 1] >= 0)
                & (self.pos[:, 1] < h)
            )

            self.pos = self.pos[alive]
            self.vel = self.vel[alive]
            self.colors = self.colors[alive]
            self.life = self.life[alive]
            self.decay = self.decay[alive]
            self.sizes = self.sizes[alive]

        # 4. Composite: Start with Clean Background (Empty Chair)
        result = self.background_plate.copy()

        # 5. Render remaining (not yet dissolved) person with subtle charred edge
        if curr_tau < 1.0:
            remaining_mask = (self.dissolve_map >= curr_tau) * self.frozen_mask

            edge_zone = (self.dissolve_map >= curr_tau) & (self.dissolve_map < curr_tau + 0.06)
            edge_factor = 1.0 - (self.dissolve_map - curr_tau) / 0.06
            edge_factor = np.clip(edge_factor * edge_zone, 0.0, 1.0)

            person_rendered = self.frozen_person.astype(np.float32)
            person_gray = np.mean(person_rendered, axis=2, keepdims=True)
            charred = person_gray * 0.4

            edge_blend = edge_factor[:, :, np.newaxis]
            person_styled = (1.0 - edge_blend) * person_rendered + edge_blend * charred

            alpha = remaining_mask[:, :, np.newaxis]
            result = (alpha * person_styled + (1.0 - alpha) * result.astype(np.float32)).astype(np.uint8)

        # 6. Render ash particles on top
        if len(self.pos) > 0:
            ix = self.pos[:, 0].astype(np.int32)
            iy = self.pos[:, 1].astype(np.int32)

            valid = (ix >= 0) & (ix < w) & (iy >= 0) & (iy < h)
            ix, iy = ix[valid], iy[valid]
            p_colors = self.colors[valid]
            p_alpha = self.life[valid, np.newaxis]

            cur_bg = result[iy, ix].astype(np.float32)
            blended = p_alpha * p_colors + (1.0 - p_alpha) * cur_bg
            result[iy, ix] = np.clip(blended, 0, 255).astype(np.uint8)

            for i in range(0, len(ix), 6):
                r = max(1, int(self.sizes[valid][i]))
                cv2.circle(result, (ix[i], iy[i]), r, p_colors[i].astype(int).tolist(), -1)

        if curr_tau >= 1.0 and len(self.pos) == 0:
            self.is_finished = True

        return result
