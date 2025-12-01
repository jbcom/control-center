# Terraform Aggregator Workspace


## Index

<ol type="I">
<li>
<details>
<summary>Sections</summary>

<ol type="I">
<li>
<a href="#terraform-workspace-dependencies">Terraform Workspace Dependencies</a>
</li>

</ol>
</details>

</li>

</ol>


## Terraform Workspace Dependencies


This Terraform workspace has dependencies that need to be run ahead of it.
This is configured automatically in the Terraform workflow for this workspace but will need to be accounted for if running manually.

They are:
* authentication
* bots
* organization
* secrets
* sso


