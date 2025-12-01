from dataclasses import dataclass, field


@dataclass
class TerraformModuleParameter:
    name: str
    json_encode: bool = field(default=False)
    base64_encode: bool = field(default=False)
    default: any = field(default=None)
    required: bool = field(default=True)
    description: str = field(default=None)
    sensitive: bool = field(default=False)
    type: str = field(default=None)
    trigger: str = field(default=None)

    def __post_init__(self):
        if self.type is not None:
            return

        if isinstance(self.default, str) or self.name.endswith("id"):
            self.type = "string"
        elif isinstance(self.default, bool):
            self.type = "bool"
        elif isinstance(self.default, int):
            self.type = "number"
        else:
            self.type = "any"

    def get_variable(self):
        variable = {"type": self.type}

        if not self.required:
            variable["default"] = self.default

        if self.description is not None:
            variable["description"] = self.description

        if self.sensitive:
            variable["sensitive"] = True

        return variable

    def get_trigger(self, disable_encoding: bool = False):
        if self.trigger is not None:
            return self.trigger

        trigger = f"var.{self.name}"

        if self.json_encode and not disable_encoding:
            trigger = f"jsonencode({trigger})"

        if self.base64_encode and not disable_encoding:
            trigger = f"base64encode({trigger})"

        return "${try(nonsensitive(" + trigger + "), " + trigger + ")}"
