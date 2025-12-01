APP_NAME := compass
COMPASS_ASSUME_ROLE_ARN := ${compass_assume_role_arn}
COPILOT_ASSUME_ROLE_ARN := ${copilot_assume_role_arn}
DOMAIN := ${zone_name}
AWS_REGION := ${region}
AWS_PROFILE := copilot_compass_assume_role

${help_target}

.PHONY: copilot-root-aws-profile
copilot-root-aws-profile: ## Set up an AWS profile locally for Compass in the root account
	@if ! aws configure list-profiles | grep -q 'compass_assume_role'; then \
	    echo "Creating compass_assume_role profile..."; \
	    aws configure set profile.compass_assume_role.role_arn $(COMPASS_ASSUME_ROLE_ARN); \
	    aws configure set profile.compass_assume_role.source_profile default; \
	    aws configure set profile.compass_assume_role.region us-east-1; \
	fi

.PHONY: copilot-compass-aws-profile
copilot-compass-aws-profile: copilot-root-aws-profile ## Set up an AWS profile locally for Compass in the Compass account
	@if ! aws configure list-profiles | grep -q "$(AWS_PROFILE)"; then \
	    echo "Creating copilot_compass_assume_role profile..."; \
	    aws configure set profile.$(AWS_PROFILE).role_arn $(COPILOT_ASSUME_ROLE_ARN); \
	    aws configure set profile.$(AWS_PROFILE).source_profile compass_assume_role; \
	    aws configure set profile.$(AWS_PROFILE).region us-east-1; \
	fi
