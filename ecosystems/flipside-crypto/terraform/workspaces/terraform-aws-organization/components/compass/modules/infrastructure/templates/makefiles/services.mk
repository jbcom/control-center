include copilot.mk

${help_target}

init-copilot-app: copilot-compass-aws-profile ## Initialize the Copilot application
	@if ! AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot app show $(APP_NAME) > /dev/null 2>&1; then \
	    AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot app init $(APP_NAME) --domain $(DOMAIN); \
	fi

upgrade-copilot-app: init-copilot-app ## Upgrade the Copilot application
	@AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot app upgrade

%{ for environment_name in environments ~}
%{ for service_name in services ~}
.PHONY: deploy-${environment_name}-${service_name}
deploy-${environment_name}-${service_name}:  upgrade-copilot-app  ## Deploy the ${environment_name} ${service_name} service using Copilot
	@AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot deploy --app $(APP_NAME) --name ${service_name} --env ${environment_name} --init-env --deploy-env --init-wkld --force

%{ endfor ~}

.PHONY: deploy-${environment_name}
deploy-${environment_name}: ${join(" ", formatlist("deploy-%s-%s", environment_name, services))} ## Deploy all ${environment_name} services using Copilot
%{ endfor ~}

.PHONY: deploy
deploy: ${join(" ", formatlist("deploy-%s", environments))} ## Deploy all services
