from __future__ import annotations

import colorsys
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from ._color import normalize_hex
from ._palette import Palette
from ._png import save_palette_png
from ._presets import list_presets, preset_label, preset_size

COLORBLIND_OPTIONS = {
    "None": None,
    "Protanopia": "protanopia",
    "Deuteranopia": "deuteranopia",
    "Tritanopia": "tritanopia",
    "Achromatopsia": "achromatopsia",
}

BACKGROUND_OPTIONS = {
    "White": "white",
    "Black": "black",
    "Light": "light",
    "Dark": "dark",
}

PRESET_OPTIONS = {"None": None}
PRESET_OPTIONS.update({preset_label(name): name for name in list_presets()})

PICKER_SIZE = 180
HUE_BAR_WIDTH = 26
PICKER_STEP = 3

APP_BG = "#F4F6F8"
PANEL_BG = "#FFFFFF"
BORDER = "#D8DEE7"
TEXT = "#161A20"
MUTED = "#667085"
EMPTY_SWATCH = "#EEF1F5"
FONT_BASE = ("Helvetica", 12)
FONT_SMALL = ("Helvetica", 10)
FONT_TITLE = ("Helvetica", 20, "bold")
FONT_SECTION = ("Helvetica", 12, "bold")
FONT_MONO = ("Menlo", 13)


def preset_palette_state(
    preset_name: str,
    n: int,
    mode: str,
    colorblind: str | None,
    background: str = "white",
    seed: int | None = None,
) -> tuple[list[str], list[bool]]:
    colors = Palette(mode=mode, seed=seed, colorblind=colorblind, background=background).preset(preset_name, n=n)
    locked_count = min(preset_size(preset_name), len(colors))
    locked = [index < locked_count for index in range(len(colors))]
    return colors, locked


class PaletteApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Paper Palette")
        self.geometry("960x700")
        self.resizable(False, False)
        self.configure(bg=APP_BG)

        self.colors: list[str | None] = []
        self.locked: list[bool] = []
        self.swatches: list[tk.Frame] = []
        self.labels: list[tk.Label] = []
        self.lock_labels: list[tk.Label] = []
        self._click_job: str | None = None

        self.n_var = tk.IntVar(value=6)
        self.mode_var = tk.StringVar(value="aesthetic")
        self.colorblind_var = tk.StringVar(value="None")
        self.background_var = tk.StringVar(value="White")
        self.preset_var = tk.StringVar(value="None")
        self.seed_enabled_var = tk.BooleanVar(value=False)
        self.seed_var = tk.StringVar(value="42")
        self.status_var = tk.StringVar(value="Set n, roll, click to lock, double-click to edit.")

        self._build_controls()
        self._build_status_bar()
        self._build_swatch_area()
        self._set_count()

    def _build_controls(self) -> None:
        header = tk.Frame(self, bg="#111827", padx=22, pady=14)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Paper Palette",
            bg="#111827",
            fg="#FFFFFF",
            font=FONT_TITLE,
        ).grid(row=0, column=0, sticky="w")
        tk.Label(
            header,
            text="Publication-ready palettes with presets, locks, export, and colorblind checks",
            bg="#111827",
            fg="#C9D2E3",
            font=FONT_SMALL,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        header.columnconfigure(0, weight=1)
        tk.Button(
            header,
            text="Roll",
            width=12,
            command=self.roll,
            bg="#FFFFFF",
            fg=TEXT,
            activebackground="#E8EEF9",
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            font=("Helvetica", 13, "bold"),
            padx=12,
            pady=7,
            cursor="hand2",
        ).grid(row=0, column=1, rowspan=2, sticky="e")

        controls = tk.Frame(
            self,
            bg=PANEL_BG,
            padx=18,
            pady=14,
            highlightthickness=1,
            highlightbackground=BORDER,
        )
        controls.pack(fill=tk.X, padx=18, pady=(16, 8))

        tk.Label(controls, text="Settings", bg=PANEL_BG, fg=TEXT, font=FONT_SECTION).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
        )

        tk.Label(controls, text="n", bg=PANEL_BG, fg=MUTED, font=FONT_SMALL).grid(row=1, column=0, pady=(10, 0), sticky="w")
        n_spin = tk.Spinbox(
            controls,
            from_=1,
            to=24,
            textvariable=self.n_var,
            width=5,
            command=self._set_count,
            font=FONT_BASE,
            relief=tk.SOLID,
            bd=1,
        )
        n_spin.grid(row=2, column=0, padx=(0, 16), sticky="w")
        n_spin.bind("<Return>", lambda _event: self._set_count())
        n_spin.bind("<FocusOut>", lambda _event: self._set_count())

        self._control_label(controls, "mode", 1, 1)
        self._option_menu(controls, self.mode_var, ("aesthetic", "categorical"), 2, 1, width=13)

        self._control_label(controls, "colorblind", 1, 2)
        self._option_menu(controls, self.colorblind_var, tuple(COLORBLIND_OPTIONS), 2, 2, width=14)

        self._control_label(controls, "background", 1, 3)
        self._option_menu(controls, self.background_var, tuple(BACKGROUND_OPTIONS), 2, 3, width=10)

        tk.Checkbutton(
            controls,
            text="Fixed seed",
            variable=self.seed_enabled_var,
            command=self._sync_seed_entry,
            bg=PANEL_BG,
            fg=TEXT,
            activebackground=PANEL_BG,
            font=FONT_SMALL,
        ).grid(row=1, column=4, pady=(10, 0), sticky="w")
        self.seed_entry = tk.Entry(
            controls,
            textvariable=self.seed_var,
            width=10,
            font=FONT_BASE,
            relief=tk.SOLID,
            bd=1,
        )
        self.seed_entry.grid(row=2, column=4, padx=(0, 20), sticky="w")

        tk.Frame(controls, height=1, bg=BORDER).grid(
            row=3,
            column=0,
            columnspan=5,
            sticky="ew",
            pady=(14, 12),
        )

        tk.Label(controls, text="Preset", bg=PANEL_BG, fg=TEXT, font=FONT_SECTION).grid(
            row=4,
            column=0,
            columnspan=2,
            sticky="w",
        )
        self._control_label(controls, "library", 5, 0)
        self._option_menu(controls, self.preset_var, tuple(PRESET_OPTIONS), 6, 0, width=18)
        tk.Button(controls, text="Apply Preset", command=self.apply_preset).grid(
            row=6,
            column=1,
            padx=(10, 18),
            sticky="ew",
        )

        tk.Label(controls, text="Actions", bg=PANEL_BG, fg=TEXT, font=FONT_SECTION).grid(
            row=4,
            column=2,
            columnspan=2,
            sticky="w",
        )
        tk.Button(controls, text="Save PNG", command=self.save_png).grid(
            row=6,
            column=2,
            padx=(0, 8),
            sticky="ew",
        )
        tk.Button(controls, text="Copy Python Array", command=self.copy_array).grid(
            row=6,
            column=3,
            padx=(0, 8),
            sticky="ew",
        )

        controls.columnconfigure(0, weight=0)
        controls.columnconfigure(3, weight=1)
        self._sync_seed_entry()

    def _control_label(self, parent: tk.Widget, text: str, row: int, column: int) -> None:
        tk.Label(parent, text=text, bg=PANEL_BG, fg=MUTED, font=FONT_SMALL).grid(
            row=row,
            column=column,
            pady=(10, 0),
            sticky="w",
        )

    def _option_menu(
        self,
        parent: tk.Widget,
        variable: tk.StringVar,
        options: tuple[str, ...],
        row: int,
        column: int,
        width: int,
    ) -> tk.OptionMenu:
        menu = tk.OptionMenu(parent, variable, *options)
        menu.configure(
            width=width,
            bg="#F8FAFC",
            fg=TEXT,
            activebackground="#EEF2F7",
            activeforeground=TEXT,
            highlightthickness=1,
            highlightbackground=BORDER,
            relief=tk.FLAT,
            font=FONT_SMALL,
        )
        menu.grid(row=row, column=column, padx=(0, 16), sticky="w")
        return menu

    def _build_status_bar(self) -> None:
        status = tk.Frame(self, bg=PANEL_BG, height=34, highlightthickness=1, highlightbackground=BORDER)
        status.pack(side=tk.BOTTOM, fill=tk.X)
        status.pack_propagate(False)
        tk.Label(
            status,
            textvariable=self.status_var,
            bg=PANEL_BG,
            fg=MUTED,
            anchor="w",
            font=FONT_SMALL,
            padx=18,
        ).pack(fill=tk.BOTH, expand=True)

    def _build_swatch_area(self) -> None:
        self.swatch_area = tk.Frame(self, bg=APP_BG, padx=18, pady=8)
        self.swatch_area.pack(fill=tk.BOTH, expand=True)

    def _sync_seed_entry(self) -> None:
        state = "normal" if self.seed_enabled_var.get() else "disabled"
        self.seed_entry.configure(state=state)

    def _current_seed(self) -> int | None:
        return self._parse_seed(self.seed_enabled_var.get(), self.seed_var.get())

    def _set_count(self) -> None:
        try:
            count = int(self.n_var.get())
        except (tk.TclError, ValueError):
            count = len(self.colors) or 1

        count = max(1, min(24, count))
        self.n_var.set(count)

        current = len(self.colors)
        if count > current:
            self.colors.extend([None] * (count - current))
            self.locked.extend([False] * (count - current))
        elif count < current:
            self.colors = self.colors[:count]
            self.locked = self.locked[:count]

        self._render_swatches()

    def _render_swatches(self) -> None:
        for child in self.swatch_area.winfo_children():
            child.destroy()
        self.swatches.clear()
        self.labels.clear()
        self.lock_labels.clear()

        count = len(self.colors)
        columns = 4 if count <= 12 else 6
        swatch_width = 206 if columns == 4 else 138
        if count <= 8:
            swatch_height = 112
            code_font = FONT_MONO
            lock_font = ("Helvetica", 9, "bold")
        elif count <= 12:
            swatch_height = 86
            code_font = ("Menlo", 11)
            lock_font = ("Helvetica", 8, "bold")
        else:
            swatch_height = 64
            code_font = ("Menlo", 9)
            lock_font = ("Helvetica", 8, "bold")

        for column in range(6):
            self.swatch_area.columnconfigure(column, weight=0)
        for row in range(6):
            self.swatch_area.rowconfigure(row, weight=0)

        for index in range(count):
            wrapper = tk.Frame(self.swatch_area, bg=APP_BG, padx=6, pady=6)
            wrapper.grid(row=index // columns, column=index % columns, sticky="nsew")

            background = self.colors[index] or EMPTY_SWATCH
            swatch = tk.Frame(
                wrapper,
                width=swatch_width,
                height=swatch_height,
                bg=background,
                highlightthickness=3 if self.locked[index] else 1,
                highlightbackground="#111827" if self.locked[index] else BORDER,
                cursor="hand2",
            )
            swatch.pack(fill=tk.BOTH, expand=True)
            swatch.pack_propagate(False)
            swatch.bind("<Button-1>", lambda _event, i=index: self.schedule_toggle_lock(i))
            swatch.bind("<Double-Button-1>", lambda _event, i=index: self.cancel_toggle_and_edit(i))

            code_label = tk.Label(
                swatch,
                text=self.colors[index] or "EMPTY",
                bg=background,
                fg=self._text_color(self.colors[index]),
                font=code_font,
            )
            code_label.pack(expand=True)
            code_label.bind("<Button-1>", lambda _event, i=index: self.schedule_toggle_lock(i))
            code_label.bind("<Double-Button-1>", lambda _event, i=index: self.cancel_toggle_and_edit(i))

            lock_label = tk.Label(
                swatch,
                text="LOCKED" if self.locked[index] else "",
                bg=background,
                fg=self._text_color(self.colors[index]),
                font=lock_font,
            )
            lock_label.pack(side=tk.BOTTOM, pady=(0, 7 if columns == 4 else 4))

            self.swatches.append(swatch)
            self.labels.append(code_label)
            self.lock_labels.append(lock_label)

        for column in range(columns):
            self.swatch_area.columnconfigure(column, weight=1)
        for row in range((count + columns - 1) // columns):
            self.swatch_area.rowconfigure(row, weight=1)

    def roll(self) -> None:
        self._set_count()
        locked_colors = [color for color, locked in zip(self.colors, self.locked) if locked and color]

        try:
            seed = self._current_seed()
            generated = Palette(
                mode=self.mode_var.get(),
                seed=seed,
                colorblind=COLORBLIND_OPTIONS[self.colorblind_var.get()],
                background=BACKGROUND_OPTIONS[self.background_var.get()],
            ).generate(len(self.colors), seed_colors=locked_colors)
        except ValueError as exc:
            messagebox.showerror("Palette error", str(exc), parent=self)
            return

        new_colors = generated[len(locked_colors) :]
        next_index = 0
        for index, locked in enumerate(self.locked):
            if locked and self.colors[index]:
                continue
            self.colors[index] = new_colors[next_index]
            next_index += 1

        seed_label = f" with seed {seed}" if seed is not None else ""
        self.status_var.set(f"Generated a new palette{seed_label}.")
        self._render_swatches()

    def apply_preset(self) -> None:
        preset_name = PRESET_OPTIONS[self.preset_var.get()]
        if preset_name is None:
            messagebox.showinfo("Preset", "Choose a preset first.", parent=self)
            return

        self._set_count()
        try:
            seed = self._current_seed()
            colors, locked = preset_palette_state(
                preset_name=preset_name,
                n=len(self.colors),
                mode=self.mode_var.get(),
                colorblind=COLORBLIND_OPTIONS[self.colorblind_var.get()],
                background=BACKGROUND_OPTIONS[self.background_var.get()],
                seed=seed,
            )
        except ValueError as exc:
            messagebox.showerror("Preset", str(exc), parent=self)
            return

        self.colors = colors
        self.locked = locked
        self.n_var.set(len(colors))
        locked_count = sum(locked)
        seed_label = f"; seed {seed}" if seed is not None else ""
        self.status_var.set(
            f"Applied preset: {self.preset_var.get()}; locked {locked_count} preset colors{seed_label}."
        )
        self._render_swatches()

    def toggle_lock(self, index: int) -> None:
        if not self.colors[index]:
            self.status_var.set("Roll first or double-click to enter a HEX color.")
            return
        self.locked[index] = not self.locked[index]
        state = "locked" if self.locked[index] else "unlocked"
        self.status_var.set(f"{self.colors[index]} {state}.")
        self._render_swatches()

    def schedule_toggle_lock(self, index: int) -> None:
        if self._click_job is not None:
            self.after_cancel(self._click_job)
        self._click_job = self.after(220, lambda: self._run_scheduled_toggle(index))

    def _run_scheduled_toggle(self, index: int) -> None:
        self._click_job = None
        self.toggle_lock(index)

    def cancel_toggle_and_edit(self, index: int) -> None:
        if self._click_job is not None:
            self.after_cancel(self._click_job)
            self._click_job = None
        self.open_hex_editor(index)

    def open_hex_editor(self, index: int) -> None:
        window = tk.Toplevel(self)
        window.title(f"Edit color {index + 1}")
        window.resizable(False, False)
        window.transient(self)
        window.grab_set()

        initial_color = normalize_hex(self.colors[index] or "#1E88E5")
        hue, saturation, value_level = self._hex_to_hsv(initial_color)
        picker_state = {"hue": hue, "saturation": saturation, "value": value_level}
        syncing = {"active": False}

        value = tk.StringVar(value=initial_color)

        body = tk.Frame(window, padx=16, pady=16)
        body.grid(row=0, column=0, sticky="nsew")

        sv_canvas = tk.Canvas(
            body,
            width=PICKER_SIZE,
            height=PICKER_SIZE,
            highlightthickness=1,
            highlightbackground="#B8B8B8",
            cursor="crosshair",
        )
        sv_canvas.grid(row=0, column=0, rowspan=4, sticky="n")

        hue_canvas = tk.Canvas(
            body,
            width=HUE_BAR_WIDTH,
            height=PICKER_SIZE,
            highlightthickness=1,
            highlightbackground="#B8B8B8",
            cursor="sb_v_double_arrow",
        )
        hue_canvas.grid(row=0, column=1, rowspan=4, padx=(10, 16), sticky="n")

        preview = tk.Frame(
            body,
            width=160,
            height=72,
            bg=value.get(),
            highlightthickness=1,
            highlightbackground="#B8B8B8",
        )
        preview.grid(row=0, column=2, columnspan=2, sticky="ew")
        preview.grid_propagate(False)

        tk.Label(body, text="HEX").grid(row=1, column=2, pady=(18, 6), sticky="w")
        entry = tk.Entry(body, textvariable=value, width=14, font=("Menlo", 13))
        entry.grid(row=1, column=3, padx=(8, 0), pady=(18, 6), sticky="w")

        error_var = tk.StringVar(value="")
        tk.Label(body, textvariable=error_var, fg="#B00020").grid(row=2, column=2, columnspan=2, sticky="w")

        def draw_hue_bar() -> None:
            hue_canvas.delete("all")
            for y in range(PICKER_SIZE):
                color = self._hsv_to_hex(y / (PICKER_SIZE - 1), 1.0, 1.0)
                hue_canvas.create_line(0, y, HUE_BAR_WIDTH, y, fill=color)
            draw_hue_marker()

        def draw_sv_plane() -> None:
            sv_canvas.delete("all")
            hue_value = picker_state["hue"]
            for x in range(0, PICKER_SIZE, PICKER_STEP):
                saturation_value = x / (PICKER_SIZE - 1)
                for y in range(0, PICKER_SIZE, PICKER_STEP):
                    brightness_value = 1.0 - (y / (PICKER_SIZE - 1))
                    color = self._hsv_to_hex(hue_value, saturation_value, brightness_value)
                    sv_canvas.create_rectangle(
                        x,
                        y,
                        x + PICKER_STEP,
                        y + PICKER_STEP,
                        fill=color,
                        outline=color,
                    )
            draw_sv_marker()

        def draw_sv_marker() -> None:
            sv_canvas.delete("marker")
            x = picker_state["saturation"] * (PICKER_SIZE - 1)
            y = (1.0 - picker_state["value"]) * (PICKER_SIZE - 1)
            radius = 6
            sv_canvas.create_oval(
                x - radius,
                y - radius,
                x + radius,
                y + radius,
                outline="#FFFFFF",
                width=2,
                tags="marker",
            )
            sv_canvas.create_oval(
                x - radius - 1,
                y - radius - 1,
                x + radius + 1,
                y + radius + 1,
                outline="#111111",
                width=1,
                tags="marker",
            )

        def draw_hue_marker() -> None:
            hue_canvas.delete("marker")
            y = picker_state["hue"] * (PICKER_SIZE - 1)
            hue_canvas.create_rectangle(
                0,
                y - 3,
                HUE_BAR_WIDTH,
                y + 3,
                outline="#111111",
                width=2,
                tags="marker",
            )
            hue_canvas.create_rectangle(
                2,
                y - 1,
                HUE_BAR_WIDTH - 2,
                y + 1,
                outline="#FFFFFF",
                width=1,
                tags="marker",
            )

        def set_value_from_picker() -> None:
            syncing["active"] = True
            value.set(
                self._hsv_to_hex(
                    picker_state["hue"],
                    picker_state["saturation"],
                    picker_state["value"],
                )
            )
            syncing["active"] = False
            refresh_preview()

        def refresh_preview(*_args: object) -> None:
            try:
                normalized = normalize_hex(value.get())
            except ValueError:
                error_var.set("Invalid HEX color.")
                return

            preview.configure(bg=normalized)
            error_var.set("")
            if syncing["active"]:
                return
            new_hue, new_saturation, new_value = self._hex_to_hsv(normalized)
            picker_state["hue"] = new_hue
            picker_state["saturation"] = new_saturation
            picker_state["value"] = new_value
            draw_sv_plane()
            draw_hue_marker()

        def select_sv(event: tk.Event) -> None:
            x = self._clamp(float(event.x), 0.0, PICKER_SIZE - 1)
            y = self._clamp(float(event.y), 0.0, PICKER_SIZE - 1)
            picker_state["saturation"] = x / (PICKER_SIZE - 1)
            picker_state["value"] = 1.0 - (y / (PICKER_SIZE - 1))
            draw_sv_marker()
            set_value_from_picker()

        def select_hue(event: tk.Event) -> None:
            y = self._clamp(float(event.y), 0.0, PICKER_SIZE - 1)
            picker_state["hue"] = y / (PICKER_SIZE - 1)
            draw_sv_plane()
            draw_hue_marker()
            set_value_from_picker()

        def apply() -> None:
            try:
                normalized = normalize_hex(value.get())
            except ValueError as exc:
                error_var.set(str(exc))
                return
            self.colors[index] = normalized
            self.locked[index] = True
            self.status_var.set(f"{normalized} set and locked.")
            self._render_swatches()
            window.destroy()

        def clear() -> None:
            self.colors[index] = None
            self.locked[index] = False
            self.status_var.set(f"Color {index + 1} cleared.")
            self._render_swatches()
            window.destroy()

        value.trace_add("write", refresh_preview)
        sv_canvas.bind("<Button-1>", select_sv)
        sv_canvas.bind("<B1-Motion>", select_sv)
        hue_canvas.bind("<Button-1>", select_hue)
        hue_canvas.bind("<B1-Motion>", select_hue)

        tk.Button(body, text="Apply", command=apply).grid(
            row=3,
            column=2,
            padx=(0, 8),
            pady=(22, 0),
            sticky="ew",
        )
        tk.Button(body, text="Clear", command=clear).grid(
            row=3,
            column=3,
            padx=(0, 0),
            pady=(22, 0),
            sticky="ew",
        )
        tk.Button(body, text="Cancel", command=window.destroy).grid(
            row=4,
            column=2,
            columnspan=2,
            pady=(8, 0),
            sticky="ew",
        )
        entry.focus_set()
        entry.select_range(0, tk.END)
        entry.bind("<Return>", lambda _event: apply())
        draw_hue_bar()
        draw_sv_plane()
        refresh_preview()

    def copy_array(self) -> None:
        colors = [color for color in self.colors if color]
        array_text = "[" + ", ".join(repr(color) for color in colors) + "]"
        self.clipboard_clear()
        self.clipboard_append(array_text)
        self.status_var.set(f"Copied {len(colors)} colors as a Python array string.")

    def save_png(self) -> None:
        colors = [color for color in self.colors if color]
        if not colors:
            messagebox.showinfo("Save palette", "Roll a palette or enter at least one HEX color first.", parent=self)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path.cwd() / "outputs" / f"palette_{timestamp}.png"
        try:
            saved_path = save_palette_png(colors, output)
        except ValueError as exc:
            messagebox.showerror("Save palette", str(exc), parent=self)
            return

        self.status_var.set(f"Saved {saved_path}.")

    @staticmethod
    def _text_color(hex_color: str | None) -> str:
        if not hex_color:
            return "#333333"
        red = int(hex_color[1:3], 16)
        green = int(hex_color[3:5], 16)
        blue = int(hex_color[5:7], 16)
        luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255.0
        return "#111111" if luminance > 0.58 else "#FFFFFF"

    @staticmethod
    def _parse_seed(enabled: bool, value: str) -> int | None:
        if not enabled:
            return None
        raw = value.strip()
        if not raw:
            raise ValueError("Seed must be an integer when Fixed seed is enabled.")
        try:
            seed = int(raw)
        except ValueError as exc:
            raise ValueError("Seed must be an integer.") from exc
        if seed < 0:
            raise ValueError("Seed must be 0 or a positive integer.")
        return seed

    @staticmethod
    def _hex_to_hsv(hex_color: str) -> tuple[float, float, float]:
        normalized = normalize_hex(hex_color)
        red = int(normalized[1:3], 16) / 255.0
        green = int(normalized[3:5], 16) / 255.0
        blue = int(normalized[5:7], 16) / 255.0
        return colorsys.rgb_to_hsv(red, green, blue)

    @staticmethod
    def _hsv_to_hex(hue: float, saturation: float, value: float) -> str:
        red, green, blue = colorsys.hsv_to_rgb(
            PaletteApp._clamp_unit(hue),
            PaletteApp._clamp_unit(saturation),
            PaletteApp._clamp_unit(value),
        )
        return f"#{round(red * 255):02X}{round(green * 255):02X}{round(blue * 255):02X}"

    @staticmethod
    def _clamp_unit(value: float) -> float:
        return PaletteApp._clamp(value, 0.0, 1.0)

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))


def main() -> None:
    app = PaletteApp()
    app.mainloop()


if __name__ == "__main__":
    main()
