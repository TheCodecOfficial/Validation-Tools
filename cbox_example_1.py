from validation_tools.scenegen import make_cbox_scene
from validation_tools.validation import ValidationSuite

val = ValidationSuite("cbox_example_1")

cbox = make_cbox_scene()

val.register_scene(cbox)
val.render()
