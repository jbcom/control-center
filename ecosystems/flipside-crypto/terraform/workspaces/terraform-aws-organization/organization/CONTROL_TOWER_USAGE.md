# AWS Control Tower Management

This directory contains the Terraform configuration for managing AWS Control Tower, including the landing zone and controls (guardrails).

## Configuration

The Control Tower configuration is stored in multiple files:

1. **Control Tower Settings**: `workspaces/aws/generator/config/control_tower.yaml`
   - Landing Zone settings (version, governed regions, centralized logging, etc.)
   - Controls to be enabled and their target organizational units
   - Controls with parameters (if any)

2. **Organizational Unit Settings**: `workspaces/aws/generator/config/units/*.yaml`
   - Each organizational unit can define a `landing_zone_name` field
   - This field specifies the name to use in Control Tower (which may differ from the AWS Organizations name)
   - Example: The "Sandbox" OU in AWS Organizations is named "Components" in Control Tower

## Adding New Controls

To add new controls, you need to:

1. Identify the control ID you want to add
2. Add it to the `controls` or `controls_with_params` section in the YAML file
3. Specify the target organizational units

Example:
```yaml
controls:
  AWS-GR_NEW_CONTROL_ID:
    description: "Description of the control"
    target_ous:
      - "sandbox"
      - "security"
```

## Using the Helpers

The `helpers` directory contains tools to help you discover and manage Control Tower controls:

### Control Catalog List Controls

The main helper is `controlcatalog_list_controls.py`, which uses the AWS Control Catalog API to list all available controls and export them to a CSV file.

To use this helper:

1. Set up a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Linux/MacOS
   .venv\Scripts\activate.bat  # On Windows
   ```

2. Install the dependencies:
   ```bash
   pip install -r helpers/requirements.txt
   ```

3. Run the script:
   ```bash
   cd helpers
   python3 controlcatalog_list_controls.py
   ```

4. Review the generated CSV file (`controlcatalog_list_controls.csv`) to find controls you want to enable

5. Add the desired controls to `workspaces/aws/generator/config/control_tower.yaml`

## Workflow

1. **Discovery**: Use the helpers to discover available controls
2. **Configuration**: Add controls to the YAML configuration file
3. **Deployment**: Apply the Terraform configuration to enable the controls

## Notes

- Controls can only be applied to organizational units, not individual accounts
- Some controls require parameters, which can be specified in the `controls_with_params` section
- The Control Tower landing zone must be set up before controls can be enabled
