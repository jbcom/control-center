from dataclasses import dataclass, field


@dataclass
class TerraformModuleEnvironmentVariable:
    name: str  # The name of the environment variable
    required: bool = field(default=True)  # Whether the environment variable is required
    sensitive: bool = field(default=False)  # Whether the environment variable is sensitive

    def get_data_block(self):
        """
        Generate the `data` block for the environment variable.
        This uses the `env_sensitive` or `env_var` Terraform provider.
        """
        data_block = {
            "id": self.name,  # Use the name of the variable as the ID
        }

        if self.required:
            data_block["required"] = True

        return data_block

    def get_trigger(self):
        """
        Generate the reference to the environment variable value from the `data` block.
        """
        data_block_type = "env_sensitive" if self.sensitive else "env_var"
        return f"${{data.{data_block_type}.{self.name}.value}}"
