include ../copilot.mk

REPOSITORY_URL := https://github.com/FlipsideCrypto/compass.git

${help_target}

%{ for environment_name in environments ~}
.PHONY: init-${environment_name}-environment
init-${environment_name}-environment: ## Initializes the ${environment_name} Copilot environment pipeline
	@AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot pipeline init \
		--app $(APP_NAME) \
		--environments \
		${environment_name} \
		--git-branch ${env_to_branch_map[environment_name]} \
		--name compass-${environment_name}-environment \
		--pipeline-type Environments \
		--url $(REPOSITORY_URL)

.PHONY: init-${environment_name}-workloads
init-${environment_name}-workloads: ## Initializes the ${environment_name} Copilot workloads pipeline
	@AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot pipeline init \
		--app $(APP_NAME) \
		--environments \
		${environment_name} \
		--git-branch ${env_to_branch_map[environment_name]} \
		--name compass-${environment_name}-workloads \
		--pipeline-type Workloads \
		--url $(REPOSITORY_URL)

.PHONY: deploy-${environment_name}-environment
deploy-${environment_name}-environment: init-${environment_name}-environment ## Deploys the ${environment_name} Copilot environment pipeline
	@AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot pipeline deploy --app $(APP_NAME) --name compass-${environment_name}-environment --yes

.PHONY: deploy-${environment_name}-workloads
deploy-${environment_name}-workloads: init-${environment_name}-workloads ## Deploys the ${environment_name} Copilot workloads pipeline
	@AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION) copilot pipeline deploy --app $(APP_NAME) --name compass-${environment_name}-workloads --yes

.PHONY: deploy-${environment_name}
deploy-${environment_name}: deploy-${environment_name}-environment deploy-${environment_name}-workloads ## Deploys all ${environment_name} Copilot pipelines
%{ endfor ~}

.PHONY: deploy
deploy: ${join(" ", formatlist("deploy-%s", environments))} ## Deploy all pipelines
