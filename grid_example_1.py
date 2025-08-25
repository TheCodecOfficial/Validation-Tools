from validation_tools.scenegen import make_mat_prev_scene, make_material
from validation_tools.validation import ValidationSuite
from validation_tools.color_util import color_range

scene = make_mat_prev_scene()
scene.set_spp(128)
scene.set_resolution(128, 128)

val = ValidationSuite("grid_example_1", nori_only=True)

for color in color_range((1, 0.25, 0), (0.9, 0.03, 0.2), n=7):
    material = make_material("diffuse", albedo=color)
    scene.set_bsdf("material_preview", material)

    val.register_scene(scene)

val.render()
val.make_grid(cell_resolution=128)
