from matplotlib.pyplot import grid
from validation_tools.nori_to_mitsuba import convert_scene
from validation_tools.exr_util import read_exr, write_exr
from PIL import Image, ImageDraw, ImageFont
import mitsuba as mi
import numpy as np
import os
import subprocess
import datetime
import cv2
from tqdm import tqdm


class ValidationSuite:
    def __init__(self, name, nori_only=False):
        self.name = name
        self.nori_only = nori_only

        self.directory = f"validation/scenes/{name}"
        self.scene_directory = f"{self.directory}/scenes"
        self.render_directory = f"{self.directory}/renders"
        self.log_directory = f"{self.directory}/logs"

        self.scenes = []
        self.scene_labels = []

        self.__setup_directories()

    def __setup_directories(self):
        os.makedirs(self.directory, exist_ok=True)
        os.makedirs(self.scene_directory, exist_ok=True)
        os.makedirs(self.render_directory, exist_ok=True)
        os.makedirs(self.log_directory, exist_ok=True)

        print(f"Created validation suite: {self.name}")

    def register_scene(self, scene, label=""):
        scene = scene.copy()
        scene_name = scene.name
        base_path = f"{self.scene_directory}/{scene_name}"

        num_scenes = len(self.scenes)

        nori_path = f"{base_path}_{num_scenes}_nori.xml"
        mitsuba_path = f"{base_path}_{num_scenes}_mitsuba.xml"

        xml_str = scene.generate()
        with open(nori_path, "w") as f:
            f.write(xml_str)

        if not self.nori_only:
            convert_scene(nori_path, mitsuba_path, verbose=False)

        scene.name = f"{scene_name}_{num_scenes}"
        self.scenes.append(scene)
        self.scene_labels.append(label)

        print(f"Generated scene {scene.name}")

    def render(self):
        iter = tqdm(self.scenes, desc="Rendering scenes") if len(self.scenes) > 1 else self.scenes
        if len(self.scenes) == 1:
            print(f"Rendering scene {self.scenes[0].name}")
        for scene in iter:

            self.__render_nori(scene)
            timestamp = datetime.datetime.now()

            with open(f"{self.log_directory}/{scene.name}_nori.log", "w") as log_file:
                log_file.write(f"Scene name: {scene.name}\n")
                log_file.write(f"Renderer: nori\n")
                log_file.write(
                    f"Integrator: {scene.desc['integrator'].kwargs['type']}\n"
                )
                log_file.write(f"Sampler: {scene.desc['sampler'].kwargs['type']}\n")
                log_file.write(
                    f"Resolution: {scene.desc['camera'].children[2].kwargs['value']} x {scene.desc['camera'].children[3].kwargs['value']}\n"
                )
                log_file.write(
                    f"SPP: {scene.desc['sampler'].children[0].kwargs['value']}\n"
                )
                log_file.write(
                    f"Renders: {scene.name}_nori.png, {scene.name}_nori.exr\n"
                )

                log_file.write(f"Rendered at {timestamp}\n")

                if not self.nori_only:
                    self.__render_mitsuba(scene)
                    timestamp = datetime.datetime.now()

                    with open(
                        f"{self.log_directory}/{scene.name}_mitsuba.log", "w"
                    ) as log_file:
                        log_file.write(f"Scene name: {scene.name}\n")
                        log_file.write(f"Renderer: mitsuba\n")
                        log_file.write(
                            f"Integrator: Mitsuba equivalent of {scene.desc['integrator'].kwargs['type']}\n"
                        )
                        log_file.write(
                            f"Sampler: {scene.desc['sampler'].kwargs['type']}\n"
                        )
                        log_file.write(
                            f"Resolution: {scene.desc['camera'].children[2].kwargs['value']} x {scene.desc['camera'].children[3].kwargs['value']}\n"
                        )
                        log_file.write(
                            f"SPP: {scene.desc['sampler'].children[0].kwargs['value']}\n"
                        )
                        log_file.write(
                            f"Renders: {scene.name}_mitsuba.png, {scene.name}_mitsuba.exr\n"
                        )

                        log_file.write(f"Rendered at {timestamp}\n")

        print(f"Rendered scenes {[scene.name for scene in self.scenes]}")

    def __render_nori(self, scene):
        NORI_BUILD_DIR = "build"

        name = f"{scene.name}_nori"

        result = subprocess.run(
            [f"./{NORI_BUILD_DIR}/nori", "-b", f"{self.scene_directory}/{name}.xml"],
            capture_output=True,
            text=True,
        )

        if not result.returncode == 0:
            print(f"Error rendering: {result.stderr}")

        # Move files to outputs
        os.rename(
            f"{self.scene_directory}/{name}.png", f"{self.render_directory}/{name}.png"
        )
        os.rename(
            f"{self.scene_directory}/{name}.exr", f"{self.render_directory}/{name}.exr"
        )

    def __render_mitsuba(self, scene):
        mi.set_variant("scalar_rgb")
        name = f"{scene.name}_mitsuba"
        scene = mi.load_file(f"{self.scene_directory}/{name}.xml")
        image = mi.render(scene)

        output_path = f"{self.render_directory}/{name}"
        mi.util.write_bitmap(f"{output_path}.png", image)
        mi.util.write_bitmap(f"{output_path}.exr", image)

    def make_grid(
        self,
        name="grid",
        rows=None,
        cols=None,
        cell_resolution=128,
        generate_labels=False,
    ):
        if rows is None and cols is None:
            cols = len(self.scenes)
            rows = 1
        elif rows is None:
            rows = (len(self.scenes) + cols - 1) // cols
        elif cols is None:
            cols = (len(self.scenes) + rows - 1) // rows

        self.__make_png_grid(name, (cols, rows), cell_resolution, generate_labels)
        self.__make_exr_grid(name, (cols, rows), cell_resolution)

    def __make_png_grid(self, name, size, resolution, generate_labels):
        nori_grid = Image.new("RGB", (size[0] * resolution, size[1] * resolution))
        mitsuba_grid = Image.new("RGB", (size[0] * resolution, size[1] * resolution))

        for i, scene in enumerate(self.scenes):
            img = Image.open(f"{self.render_directory}/{scene.name}_nori.png")
            img = img.resize((resolution, resolution))
            nori_grid.paste(img, (i % size[0] * resolution, i // size[0] * resolution))

            if not self.nori_only:
                img = Image.open(f"{self.render_directory}/{scene.name}_mitsuba.png")
                img = img.resize((resolution, resolution))
                mitsuba_grid.paste(
                    img, (i % size[0] * resolution, i // size[0] * resolution)
                )

        nori_grid.save(f"{self.render_directory}/{name}_nori.png")

        if not self.nori_only:
            mitsuba_grid.save(f"{self.render_directory}/{name}_mitsuba.png")

        if generate_labels:
            resolution = 256
            nori_grid = nori_grid.resize((resolution, resolution))
            draw = ImageDraw.Draw(nori_grid)
            font = ImageFont.load_default(size=24)
            for i, scene in enumerate(self.scene_labels):
                label = self.scene_labels[i]
                bbox = draw.textbbox((0, 0), label, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = (
                    (i % size[0] + 0.5) * resolution - text_width // 2,
                    (i // size[0] + 0.5) * resolution - text_height // 2,
                )
                draw.text(
                    position,
                    label,
                    fill="white",
                    align="center",
                    font=font,
                    stroke_fill="black",
                    stroke_width=3,
                )
            nori_grid.save(f"{self.render_directory}/{name}_nori_labeled.png")

    def __make_exr_grid(self, name, size, resolution):
        nori_grid = np.zeros(
            (size[1] * resolution, size[0] * resolution, 3), dtype=np.float32
        )
        mitsuba_grid = np.zeros(
            (size[1] * resolution, size[0] * resolution, 3), dtype=np.float32
        )

        for i, scene in enumerate(self.scenes):
            img = read_exr(f"{self.render_directory}/{scene.name}_nori.exr")
            img = cv2.resize(
                img, (resolution, resolution), interpolation=cv2.INTER_CUBIC
            )
            nori_grid[
                (i // size[0]) * resolution : (i // size[0] + 1) * resolution,
                (i % size[0]) * resolution : (i % size[0] + 1) * resolution,
            ] = img

            if not self.nori_only:
                img = read_exr(f"{self.render_directory}/{scene.name}_mitsuba.exr")
                img = cv2.resize(
                    img, (resolution, resolution), interpolation=cv2.INTER_CUBIC
                )
                mitsuba_grid[
                    (i // size[0]) * resolution : (i // size[0] + 1) * resolution,
                    (i % size[0]) * resolution : (i % size[0] + 1) * resolution,
                ] = img

        write_exr(f"{self.render_directory}/{name}_nori.exr", nori_grid)
        if not self.nori_only:
            write_exr(f"{self.render_directory}/{name}_mitsuba.exr", mitsuba_grid)
