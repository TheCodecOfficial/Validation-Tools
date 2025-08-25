from validation_tools.scenegen import make_mat_prev_scene, make_material
from validation_tools.validation import ValidationSuite
from validation_tools.color_util import color_range, color_to_str

scene = make_mat_prev_scene()
scene.set_spp(128)
scene.set_resolution(128, 128)

val = ValidationSuite("grid_example_2", nori_only=True)

for color in color_range((0.01, 0.1, 0.3), (0.5, 0, 0.05), n=5, use_oklab=True):
    for alpha in [0.001, 0.1, 0.25, 0.5, 1]:
        material = make_material("microfacet", kd=color, alpha=alpha)
        scene.set_bsdf("material_preview", material)

        val.register_scene(scene, label=f"alpha: {alpha:.3f}\n{color_to_str(color)}")

val.render()
val.make_grid("color_roughness_grid", cell_resolution=128, cols=5, generate_labels=True)
