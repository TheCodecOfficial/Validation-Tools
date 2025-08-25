from validation_tools.scenegen import make_cbox_scene, make_material
from validation_tools.validation import ValidationSuite

val = ValidationSuite("cbox_example_2")

cbox = make_cbox_scene(
    "custom_cbox",
    left_wall_color=(0.15, 0.2, 1),
    right_wall_color=(0.95, 0.4, 0),
    emitter_color=(5, 5, 5),
    main_wall_color=(0.5, 0.5, 0.5),
    cuboid_color=(1, 0, 0.2),
)
cbox.set_quality("m")

mirror = make_material("mirror")
cbox.set_bsdf("ball", mirror)

val.register_scene(cbox)
val.render()
