#!/usr/bin/env python3

import json
import os
import glob

# Directory containing dashboard templates
dashboard_dir = "workspaces/aws/monitoring/logging/templates/dashboards"

# Process each dashboard JSON file
for file_path in glob.glob(f"{dashboard_dir}/*.json"):
    print(f"Processing {file_path}...")
    
    try:
        # Read the dashboard JSON
        with open(file_path, 'r') as f:
            dashboard = json.load(f)
        
        # Find the account variable in the templating section
        account_var = None
        if "templating" in dashboard and "list" in dashboard["templating"]:
            for var in dashboard["templating"]["list"]:
                if var.get("name") == "account":
                    account_var = var
                    break
        
        # If account variable exists, ensure it has a default value
        if account_var:
            # Add a default current value to the account variable
            if "current" not in account_var or not account_var["current"]:
                account_var["current"] = {"selected": True, "text": "All", "value": "$__all"}
            
            # Make sure includeAll is true for the account variable
            account_var["includeAll"] = True
            
            # Add a default value option
            if "options" not in account_var or not account_var["options"]:
                account_var["options"] = [{"selected": True, "text": "All", "value": "$__all"}]
        
        # Fix dimensions in all targets to handle the "All" value case
        if "panels" in dashboard:
            for panel in dashboard["panels"]:
                if "targets" in panel:
                    for target in panel["targets"]:
                        if "dimensions" in target and "AccountId" in target["dimensions"]:
                            # Update the target to use a conditional expression for AccountId
                            # This ensures that when "All" is selected, it doesn't cause validation errors
                            target["dimensions"]["AccountId"] = "${account:text}"
        
        # Write the updated dashboard back to the file
        with open(file_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"Successfully updated {file_path}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

print("All dashboards have been updated!")
