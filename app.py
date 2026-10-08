import os
import sys
import time
import math
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import cv2
from PIL import Image, ImageTk

from converter import get_video_info, convert_video_to_gif

# Appearance Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class VideoToGifApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Video to GIF Converter")
        self.geometry("1100x720")
        self.minsize(950, 650)

        # Video State Variables
        self.video_path = None
        self.cap = None
        self.duration = 0.0
        self.total_frames = 0
        self.fps = 25.0
        self.width = 0
        self.height = 0
        self.current_frame = 0

        # Playback State
        self.is_playing = False
        self.play_thread = None
        self.stop_play_event = threading.Event()

        # Trim & Speed Settings
        self.start_time = 0.0
        self.end_time = 0.0
        self.speed = 1.0
        self.preview_trimmed_loop_only = False

        # Conversion State
        self.is_converting = False

        # UI Setup
        self._build_ui()

    def _build_ui(self):
        # Main layout grid (Left: Video Player, Right: Controls)
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # Left Panel (Video Display & Transport Controls)
        self.left_panel = ctk.CTkFrame(self, corner_radius=10)
        self.left_panel.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        self.left_panel.grid_rowconfigure(1, weight=1)
        self.left_panel.grid_columnconfigure(0, weight=1)

        # Top Bar: File Selection
        self.top_bar = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.top_bar.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.btn_open = ctk.CTkButton(
            self.top_bar, text="📁 Open Video File", font=("Segoe UI", 13, "bold"), command=self.open_file, height=36
        )
        self.btn_open.pack(side="left", padx=5)

        self.lbl_filename = ctk.CTkLabel(
            self.top_bar, text="No video selected", font=("Segoe UI", 12), text_color="gray"
        )
        self.lbl_filename.pack(side="left", padx=10, fill="x", expand=True)

        # Video Canvas / Frame display container
        self.video_container = ctk.CTkFrame(self.left_panel, fg_color="#181818", corner_radius=8)
        self.video_container.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.video_container.grid_rowconfigure(0, weight=1)
        self.video_container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.video_container, bg="#101010", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Player Control Bar
        self.player_controls = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.player_controls.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # Timeline Scrubber
        self.slider_scrubber = ctk.CTkSlider(
            self.player_controls, from_=0, to=100, command=self.on_scrub, state="disabled"
        )
        self.slider_scrubber.set(0)
        self.slider_scrubber.pack(fill="x", padx=5, pady=(0, 5))

        # Playback Buttons & Time Counter
        self.controls_sub = ctk.CTkFrame(self.player_controls, fg_color="transparent")
        self.controls_sub.pack(fill="x", padx=5)

        self.btn_prev_frame = ctk.CTkButton(
            self.controls_sub, text="⏮", width=40, height=32, command=self.step_prev_frame, state="disabled"
        )
        self.btn_prev_frame.pack(side="left", padx=2)

        self.btn_play = ctk.CTkButton(
            self.controls_sub, text="▶ Play", width=80, height=32, command=self.toggle_play, state="disabled"
        )
        self.btn_play.pack(side="left", padx=5)

        self.btn_next_frame = ctk.CTkButton(
            self.controls_sub, text="⏭", width=40, height=32, command=self.step_next_frame, state="disabled"
        )
        self.btn_next_frame.pack(side="left", padx=2)

        self.lbl_time = ctk.CTkLabel(
            self.controls_sub, text="00:00.00 / 00:00.00", font=("Consolas", 13, "bold")
        )
        self.lbl_time.pack(side="right", padx=10)

        # Right Panel (Trim, Speed, GIF Quality Settings & Export)
        self.right_panel = ctk.CTkScrollableFrame(self, corner_radius=10, label_text="GIF Settings & Controls")
        self.right_panel.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")

        # --- SECTION 1: CLIP / TRIM CONTROL ---
        self.frame_trim = ctk.CTkFrame(self.right_panel, corner_radius=8)
        self.frame_trim.pack(fill="x", padx=10, pady=8)

        lbl_trim_title = ctk.CTkLabel(self.frame_trim, text="✂ Clip / Trim Video", font=("Segoe UI", 14, "bold"))
        lbl_trim_title.pack(anchor="w", padx=12, pady=(10, 5))

        # Set Start / End Buttons
        trim_btn_frame = ctk.CTkFrame(self.frame_trim, fg_color="transparent")
        trim_btn_frame.pack(fill="x", padx=10, pady=5)

        self.btn_set_start = ctk.CTkButton(
            trim_btn_frame, text="Set Start at Current", font=("Segoe UI", 11), command=self.set_start_current, state="disabled"
        )
        self.btn_set_start.pack(side="left", expand=True, fill="x", padx=3)

        self.btn_set_end = ctk.CTkButton(
            trim_btn_frame, text="Set End at Current", font=("Segoe UI", 11), command=self.set_end_current, state="disabled"
        )
        self.btn_set_end.pack(side="left", expand=True, fill="x", padx=3)

        # Start Time Slider & Input
        lbl_start = ctk.CTkLabel(self.frame_trim, text="Start Time (sec):", font=("Segoe UI", 11))
        lbl_start.pack(anchor="w", padx=12, pady=(5, 0))

        start_input_frame = ctk.CTkFrame(self.frame_trim, fg_color="transparent")
        start_input_frame.pack(fill="x", padx=10, pady=2)

        self.slider_start = ctk.CTkSlider(start_input_frame, from_=0, to=100, command=self.on_start_slider, state="disabled")
        self.slider_start.set(0)
        self.slider_start.pack(side="left", fill="x", expand=True, padx=3)

        self.entry_start = ctk.CTkEntry(start_input_frame, width=65, font=("Consolas", 12))
        self.entry_start.insert(0, "0.00")
        self.entry_start.pack(side="right", padx=3)
        self.entry_start.bind("<Return>", self.on_start_entry_change)

        # End Time Slider & Input
        lbl_end = ctk.CTkLabel(self.frame_trim, text="End Time (sec):", font=("Segoe UI", 11))
        lbl_end.pack(anchor="w", padx=12, pady=(5, 0))

        end_input_frame = ctk.CTkFrame(self.frame_trim, fg_color="transparent")
        end_input_frame.pack(fill="x", padx=10, pady=2)

        self.slider_end = ctk.CTkSlider(end_input_frame, from_=0, to=100, command=self.on_end_slider, state="disabled")
        self.slider_end.set(100)
        self.slider_end.pack(side="left", fill="x", expand=True, padx=3)

        self.entry_end = ctk.CTkEntry(end_input_frame, width=65, font=("Consolas", 12))
        self.entry_end.insert(0, "0.00")
        self.entry_end.pack(side="right", padx=3)
        self.entry_end.bind("<Return>", self.on_end_entry_change)

        # Trimmed duration info
        self.lbl_trim_duration = ctk.CTkLabel(
            self.frame_trim, text="Selected Duration: 0.00s", font=("Segoe UI", 11, "bold"), text_color="#3B8ED0"
        )
        self.lbl_trim_duration.pack(anchor="w", padx=12, pady=(5, 10))

        # --- SECTION 2: SPEED CONTROL ---
        self.frame_speed = ctk.CTkFrame(self.right_panel, corner_radius=8)
        self.frame_speed.pack(fill="x", padx=10, pady=8)

        lbl_speed_title = ctk.CTkLabel(self.frame_speed, text="⚡ Speed Multiplier", font=("Segoe UI", 14, "bold"))
        lbl_speed_title.pack(anchor="w", padx=12, pady=(10, 5))

        lbl_speed_desc = ctk.CTkLabel(
            self.frame_speed, text="Adjust speed to match your target GIF loop timing.", font=("Segoe UI", 10), text_color="gray"
        )
        lbl_speed_desc.pack(anchor="w", padx=12, pady=(0, 5))

        # Speed Quick Buttons
        speed_btn_frame = ctk.CTkFrame(self.frame_speed, fg_color="transparent")
        speed_btn_frame.pack(fill="x", padx=10, pady=5)

        for spd_val in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
            btn = ctk.CTkButton(
                speed_btn_frame,
                text=f"{spd_val}x",
                width=42,
                height=26,
                font=("Segoe UI", 10, "bold"),
                command=lambda v=spd_val: self.set_speed(v)
            )
            btn.pack(side="left", expand=True, padx=2)

        # Speed Slider & Display
        speed_slider_frame = ctk.CTkFrame(self.frame_speed, fg_color="transparent")
        speed_slider_frame.pack(fill="x", padx=10, pady=5)

        self.slider_speed = ctk.CTkSlider(speed_slider_frame, from_=0.25, to=4.0, number_of_steps=75, command=self.on_speed_slider)
        self.slider_speed.set(1.0)
        self.slider_speed.pack(side="left", fill="x", expand=True, padx=3)

        self.lbl_speed_val = ctk.CTkLabel(speed_slider_frame, text="1.00x", font=("Consolas", 12, "bold"), width=55)
        self.lbl_speed_val.pack(side="right", padx=3)

        # Effective GIF Duration info
        self.lbl_gif_duration = ctk.CTkLabel(
            self.frame_speed, text="Effective GIF Playback: 0.00s", font=("Segoe UI", 11, "bold"), text_color="#2FA572"
        )
        self.lbl_gif_duration.pack(anchor="w", padx=12, pady=(5, 10))

        # --- SECTION 3: GIF RESOLUTION & FPS ---
        self.frame_gif_opt = ctk.CTkFrame(self.right_panel, corner_radius=8)
        self.frame_gif_opt.pack(fill="x", padx=10, pady=8)

        lbl_opt_title = ctk.CTkLabel(self.frame_gif_opt, text="⚙ GIF Export Settings", font=("Segoe UI", 14, "bold"))
        lbl_opt_title.pack(anchor="w", padx=12, pady=(10, 5))

        # Width / Resolution
        res_frame = ctk.CTkFrame(self.frame_gif_opt, fg_color="transparent")
        res_frame.pack(fill="x", padx=10, pady=4)

        lbl_res = ctk.CTkLabel(res_frame, text="Width (px):", font=("Segoe UI", 11))
        lbl_res.pack(side="left", padx=5)

        self.combo_width = ctk.CTkComboBox(
            res_frame, values=["320 (Small)", "480 (Medium)", "640 (Large)", "720 (HD)", "Original"], width=140
        )
        self.combo_width.set("480 (Medium)")
        self.combo_width.pack(side="right", padx=5)

        # FPS
        fps_frame = ctk.CTkFrame(self.frame_gif_opt, fg_color="transparent")
        fps_frame.pack(fill="x", padx=10, pady=4)

        lbl_fps = ctk.CTkLabel(fps_frame, text="Frame Rate (FPS):", font=("Segoe UI", 11))
        lbl_fps.pack(side="left", padx=5)

        self.combo_fps = ctk.CTkComboBox(
            fps_frame, values=["10 FPS", "15 FPS (Recommended)", "20 FPS", "24 FPS", "30 FPS"], width=170
        )
        self.combo_fps.set("15 FPS (Recommended)")
        self.combo_fps.pack(side="right", padx=5)

        # Quality Mode
        qual_frame = ctk.CTkFrame(self.frame_gif_opt, fg_color="transparent")
        qual_frame.pack(fill="x", padx=10, pady=4)

        lbl_qual = ctk.CTkLabel(qual_frame, text="Color Quality:", font=("Segoe UI", 11))
        lbl_qual.pack(side="left", padx=5)

        self.combo_quality = ctk.CTkComboBox(
            qual_frame, values=["High (PaletteGen)", "Fast Standard"], width=170
        )
        self.combo_quality.set("High (PaletteGen)")
        self.combo_quality.pack(side="right", padx=5)

        # --- SECTION 4: EXPORT BUTTON & PROGRESS ---
        self.frame_export = ctk.CTkFrame(self.right_panel, corner_radius=8, fg_color="transparent")
        self.frame_export.pack(fill="x", padx=10, pady=12)

        self.btn_convert = ctk.CTkButton(
            self.frame_export,
            text="🎥 Convert to GIF",
            font=("Segoe UI", 15, "bold"),
            height=46,
            fg_color="#2FA572",
            hover_color="#218557",
            command=self.start_conversion,
            state="disabled"
        )
        self.btn_convert.pack(fill="x", pady=5)

        self.progress_bar = ctk.CTkProgressBar(self.frame_export)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=5)

        self.lbl_status = ctk.CTkLabel(self.frame_export, text="Ready", font=("Segoe UI", 11), text_color="gray")
        self.lbl_status.pack(pady=2)

    # --- VIDEO LOADING & PLAYER METHODS ---
    def open_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv *.webm *.flv *.wmv *.m4v"),
                ("All Files", "*.*")
            ]
        )
        if not filepath:
            return

        try:
            info = get_video_info(filepath)
        except Exception as e:
            messagebox.showerror("Error Opening Video", f"Could not load video metadata:\n{str(e)}")
            return

        self.video_path = filepath
        self.duration = info["duration"]
        self.total_frames = info["total_frames"]
        self.fps = info["fps"]
        self.width = info["width"]
        self.height = info["height"]

        # Stop playback if currently playing
        self.stop_playback()

        # Update Open File OpenCV Capture
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(filepath)

        # Reset Trim Sliders & Inputs
        self.start_time = 0.0
        self.end_time = self.duration

        self.slider_start.configure(state="normal", from_=0, to=self.duration)
        self.slider_start.set(0)
        self.entry_start.delete(0, tk.END)
        self.entry_start.insert(0, "0.00")

        self.slider_end.configure(state="normal", from_=0, to=self.duration)
        self.slider_end.set(self.duration)
        self.entry_end.delete(0, tk.END)
        self.entry_end.insert(0, f"{self.duration:.2f}")

        self.slider_scrubber.configure(state="normal", from_=0, to=max(1, self.total_frames - 1))
        self.slider_scrubber.set(0)

        self.btn_play.configure(state="normal")
        self.btn_prev_frame.configure(state="normal")
        self.btn_next_frame.configure(state="normal")
        self.btn_set_start.configure(state="normal")
        self.btn_set_end.configure(state="normal")
        self.btn_convert.configure(state="normal")

        # UI Labels update
        filename_only = os.path.basename(filepath)
        self.lbl_filename.configure(
            text=f"{filename_only} ({self.width}x{self.height}, {self.fps:.1f} FPS)",
            text_color="white"
        )

        self.update_trim_durations()

        # Show first frame
        self.seek_to_frame(0)

    def update_trim_durations(self):
        trimmed_len = max(0.0, self.end_time - self.start_time)
        self.lbl_trim_duration.configure(text=f"Selected Duration: {trimmed_len:.2f}s")

        eff_len = trimmed_len / self.speed if self.speed > 0 else 0.0
        self.lbl_gif_duration.configure(text=f"Effective GIF Playback: {eff_len:.2f}s")

    def seek_to_frame(self, frame_num):
        if not self.cap or not self.cap.isOpened():
            return

        frame_num = max(0, min(self.total_frames - 1, int(frame_num)))
        self.current_frame = frame_num
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = self.cap.read()

        if ret:
            self.display_frame(frame)
            current_sec = frame_num / self.fps if self.fps > 0 else 0
            self.lbl_time.configure(text=f"{self.format_time(current_sec)} / {self.format_time(self.duration)}")
            self.slider_scrubber.set(frame_num)

    def display_frame(self, cv2_frame):
        if cv2_frame is None:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if cw <= 10 or ch <= 10:
            cw, ch = 640, 360

        # Ultra-fast C++ OpenCV resize before PIL conversion
        img_h, img_w = cv2_frame.shape[:2]
        ratio = min(cw / img_w, ch / img_h)
        new_w = max(1, int(img_w * ratio))
        new_h = max(1, int(img_h * ratio))

        resized_bgr = cv2.resize(cv2_frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        rgb_frame = cv2.cvtColor(resized_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_frame)
        self.tk_image = ImageTk.PhotoImage(pil_img)

        self.canvas.delete("all")
        pos_x = (cw - new_w) // 2
        pos_y = (ch - new_h) // 2
        self.canvas.create_image(pos_x, pos_y, anchor="nw", image=self.tk_image)

    def on_canvas_resize(self, event):
        if self.video_path and self.cap:
            self.seek_to_frame(self.current_frame)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:05.2f}"

    def on_scrub(self, val):
        if not self.is_playing:
            self.seek_to_frame(val)

    def step_prev_frame(self):
        self.stop_playback()
        self.seek_to_frame(self.current_frame - 1)

    def step_next_frame(self):
        self.stop_playback()
        self.seek_to_frame(self.current_frame + 1)

    # --- PLAYBACK THREADING ---
    def toggle_play(self):
        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        if not self.cap or self.is_playing:
            return

        self.is_playing = True
        self.btn_play.configure(text="⏸ Pause")
        self.stop_play_event.clear()

        # Start playback thread
        self.play_thread = threading.Thread(target=self._play_loop, daemon=True)
        self.play_thread.start()

    def stop_playback(self):
        self.is_playing = False
        self.btn_play.configure(text="▶ Play")
        self.stop_play_event.set()

    def _play_loop(self):
        base_delay = 1.0 / self.fps if self.fps > 0 else 0.033
        last_time = time.time()

        # Set initial frame position if outside range
        start_frame = int(self.start_time * self.fps)
        end_frame = int(self.end_time * self.fps)
        if self.current_frame >= end_frame or self.current_frame < start_frame:
            self.current_frame = start_frame
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.current_frame)

        while not self.stop_play_event.is_set() and self.is_playing:
            # Dynamically recalculate trim boundaries in real-time
            start_frame = max(0, int(self.start_time * self.fps))
            end_frame = min(self.total_frames, int(self.end_time * self.fps))

            target_delay = base_delay / self.speed if self.speed > 0 else base_delay
            now = time.time()
            elapsed = now - last_time

            if elapsed < target_delay:
                time.sleep(max(0.001, target_delay - elapsed))

            last_time = time.time()

            # Dynamic Live Boundary Check: seek/loop instantly if current position falls outside active trim range
            if self.current_frame >= end_frame or self.current_frame < start_frame:
                self.current_frame = start_frame
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

            ret, frame = self.cap.read()
            if not ret:
                self.current_frame = start_frame
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                ret, frame = self.cap.read()
                if not ret:
                    break

            self.current_frame += 1

            # Render frame on GUI thread
            self.after(0, self._render_playback_frame, frame, self.current_frame)

        self.after(0, lambda: self.btn_play.configure(text="▶ Play"))
        self.is_playing = False

    def _render_playback_frame(self, frame, frame_num):
        if not self.is_playing:
            return
        self.display_frame(frame)
        current_sec = frame_num / self.fps if self.fps > 0 else 0
        self.lbl_time.configure(text=f"{self.format_time(current_sec)} / {self.format_time(self.duration)}")
        self.slider_scrubber.set(frame_num)

    # --- TRIM CONTROLS ---
    def set_start_current(self):
        curr_sec = self.current_frame / self.fps if self.fps > 0 else 0
        if curr_sec >= self.end_time:
            curr_sec = max(0.0, self.end_time - 0.1)

        self.start_time = curr_sec
        self.slider_start.set(curr_sec)
        self.entry_start.delete(0, tk.END)
        self.entry_start.insert(0, f"{curr_sec:.2f}")
        self.update_trim_durations()

    def set_end_current(self):
        curr_sec = self.current_frame / self.fps if self.fps > 0 else 0
        if curr_sec <= self.start_time:
            curr_sec = min(self.duration, self.start_time + 0.1)

        self.end_time = curr_sec
        self.slider_end.set(curr_sec)
        self.entry_end.delete(0, tk.END)
        self.entry_end.insert(0, f"{curr_sec:.2f}")
        self.update_trim_durations()

    def on_start_slider(self, val):
        if val >= self.end_time:
            val = max(0.0, self.end_time - 0.1)
            self.slider_start.set(val)

        self.start_time = val
        self.entry_start.delete(0, tk.END)
        self.entry_start.insert(0, f"{val:.2f}")
        self.update_trim_durations()

    def on_end_slider(self, val):
        if val <= self.start_time:
            val = min(self.duration, self.start_time + 0.1)
            self.slider_end.set(val)

        self.end_time = val
        self.entry_end.delete(0, tk.END)
        self.entry_end.insert(0, f"{val:.2f}")
        self.update_trim_durations()

    def on_start_entry_change(self, event):
        try:
            val = float(self.entry_start.get())
            val = max(0.0, min(self.end_time - 0.1, val))
            self.start_time = val
            self.slider_start.set(val)
            self.entry_start.delete(0, tk.END)
            self.entry_start.insert(0, f"{val:.2f}")
            self.update_trim_durations()
        except ValueError:
            pass

    def on_end_entry_change(self, event):
        try:
            val = float(self.entry_end.get())
            val = max(self.start_time + 0.1, min(self.duration, val))
            self.end_time = val
            self.slider_end.set(val)
            self.entry_end.delete(0, tk.END)
            self.entry_end.insert(0, f"{val:.2f}")
            self.update_trim_durations()
        except ValueError:
            pass

    # --- SPEED CONTROLS ---
    def set_speed(self, speed_val):
        self.speed = speed_val
        self.slider_speed.set(speed_val)
        self.lbl_speed_val.configure(text=f"{speed_val:.2f}x")
        self.update_trim_durations()

    def on_speed_slider(self, val):
        self.speed = val
        self.lbl_speed_val.configure(text=f"{val:.2f}x")
        self.update_trim_durations()

    # --- CONVERSION LOGIC ---
    def start_conversion(self):
        if not self.video_path or self.is_converting:
            return

        if self.end_time <= self.start_time:
            messagebox.showerror("Invalid Trim Range", "End time must be greater than start time.")
            return

        # Prompt destination GIF file path
        base_name = os.path.splitext(os.path.basename(self.video_path))[0]
        default_out = f"{base_name}_output.gif"

        output_path = filedialog.asksaveasfilename(
            title="Save GIF File As",
            initialfile=default_out,
            defaultextension=".gif",
            filetypes=[("GIF Image", "*.gif")]
        )
        if not output_path:
            return

        # Parse settings
        # Width
        width_str = self.combo_width.get()
        if "320" in width_str:
            target_width = 320
        elif "480" in width_str:
            target_width = 480
        elif "640" in width_str:
            target_width = 640
        elif "720" in width_str:
            target_width = 720
        else:
            target_width = -1  # Original

        # FPS
        fps_str = self.combo_fps.get()
        target_fps = int(fps_str.split()[0])

        # Quality
        qual_str = self.combo_quality.get()
        quality_mode = "High" if "High" in qual_str else "Fast"

        # Lock UI
        self.is_converting = True
        self.btn_convert.configure(state="disabled", text="⏳ Converting...")
        self.progress_bar.set(0.2)
        self.lbl_status.configure(text="Encoding GIF with FFmpeg...", text_color="#3B8ED0")

        # Run conversion in background thread
        threading.Thread(
            target=self._conversion_worker,
            args=(output_path, target_width, target_fps, quality_mode),
            daemon=True
        ).start()

    def _conversion_worker(self, output_path, target_width, target_fps, quality_mode):
        try:
            convert_video_to_gif(
                input_path=self.video_path,
                output_path=output_path,
                start_time=self.start_time,
                end_time=self.end_time,
                speed=self.speed,
                target_fps=target_fps,
                target_width=target_width,
                quality=quality_mode
            )

            self.after(0, self._on_conversion_success, output_path)
        except Exception as e:
            self.after(0, self._on_conversion_error, str(e))

    def _on_conversion_success(self, output_path):
        self.is_converting = False
        self.progress_bar.set(1.0)
        self.btn_convert.configure(state="normal", text="🎥 Convert to GIF")
        self.lbl_status.configure(text="✅ Conversion Complete!", text_color="#2FA572")

        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)

        msg = f"GIF saved successfully!\n\nPath: {output_path}\nFile Size: {file_size_mb:.2f} MB"
        res = messagebox.askyesno("Success", f"{msg}\n\nWould you like to open the output folder?")
        if res:
            os.startfile(os.path.dirname(output_path))

    def _on_conversion_error(self, err_msg):
        self.is_converting = False
        self.progress_bar.set(0)
        self.btn_convert.configure(state="normal", text="🎥 Convert to GIF")
        self.lbl_status.configure(text="❌ Conversion Failed", text_color="#D9534F")
        messagebox.showerror("Conversion Failed", f"An error occurred during conversion:\n\n{err_msg}")


if __name__ == "__main__":
    app = VideoToGifApp()
    app.mainloop()
