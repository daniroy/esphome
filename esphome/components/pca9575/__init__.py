from esphome import pins
import esphome.codegen as cg
from esphome.components import i2c
import esphome.config_validation as cv
from esphome.const import (
    CONF_ID,
    CONF_INPUT,
    CONF_INVERTED,
    CONF_MODE,
    CONF_NUMBER,
    CONF_OUTPUT,
)

CODEOWNERS = ["@hwstar", "@clydebarrow"]
DEPENDENCIES = ["i2c"]
MULTI_CONF = True
CONF_PIN_COUNT = "pin_count"
pca9575_ns = cg.esphome_ns.namespace("pca9575")

PCA9575Component = pca9575_ns.class_("PCA9575Component", cg.Component, i2c.I2CDevice)
PCA9575GPIOPin = pca9575_ns.class_(
    "PCA9575GPIOPin", cg.GPIOPin, cg.Parented.template(PCA9575Component)
)

CONF_PCA9575 = "pca9575"
CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.Required(CONF_ID): cv.declare_id(PCA9575Component),
            cv.Optional(CONF_PIN_COUNT, default=8): cv.one_of(16),
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
    .extend(
        i2c.i2c_device_schema(0x20)
    )  # Note: 0x20 for the non-A part. The PCA9575A parts start at addess 0x38
)


async def to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    cg.add(var.set_pin_count(config[CONF_PIN_COUNT]))
    await cg.register_component(var, config)
    await i2c.register_i2c_device(var, config)


def validate_mode(value):
    if not (value[CONF_INPUT] or value[CONF_OUTPUT]):
        raise cv.Invalid("Mode must be either input or output")
    if value[CONF_INPUT] and value[CONF_OUTPUT]:
        raise cv.Invalid("Mode must be either input or output")
    return value


PCA9575_PIN_SCHEMA = pins.gpio_base_schema(
    PCA9575GPIOPin,
    cv.int_range(min=0, max=15),
    modes=[CONF_INPUT, CONF_OUTPUT],
    mode_validator=validate_mode,
).extend(
    {
        cv.Required(CONF_PCA9575): cv.use_id(PCA9575Component),
    }
)


def pca9575_pin_final_validate(pin_config, parent_config):
    count = parent_config[CONF_PIN_COUNT]
    if pin_config[CONF_NUMBER] >= count:
        raise cv.Invalid(f"Pin number must be in range 0-{count - 1}")


@pins.PIN_SCHEMA_REGISTRY.register(
    CONF_PCA9575, PCA9575_PIN_SCHEMA, pca9575_pin_final_validate
)
async def pca9575_pin_to_code(config):
    var = cg.new_Pvariable(config[CONF_ID])
    parent = await cg.get_variable(config[CONF_PCA9575])

    cg.add(var.set_parent(parent))

    num = config[CONF_NUMBER]
    cg.add(var.set_pin(num))
    cg.add(var.set_inverted(config[CONF_INVERTED]))
    cg.add(var.set_flags(pins.gpio_flags_expr(config[CONF_MODE])))
    return var
