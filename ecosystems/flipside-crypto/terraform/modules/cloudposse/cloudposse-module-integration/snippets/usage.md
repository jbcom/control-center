We leverage [CloudPosse](https://github.com/cloudposse) modules and have designed our own Terraform to be as compatible with their modules as possible.

CloudPosse provides an excellent set of curated, well-supported, standardized Terraform modules for infrastructure resources on AWS.

It is entirely possible to build out new infrastructure for an account using a YAML configuration file versus building out the Terraform yourself.

The advantage is that the infrastructure built will have its naming standardized and there is no need to maintain custom Terraform code for the component.

It is all handled by the automated systems in place.

Note that this is **not required** and infrastructure can also be built by any other means provided the guidelines on tagging are followed.

In all cases if you do not build infrastructure assets using the automated systems in this repository the level of support for the infrastructure you build will be lessened since the solution will be bespoke versus standardized.

In cases when further automation relying on the assets is planned, like in another Terraform repository that consumes infrastructure data from this one and then uses parameters, it should be in almost all cases the case that infrastructure is built here.

This will allow for easy support for downstream Terraform repositories.

Categories available for configuration are:

<dl>
%{ for category_name, category_data in categories ~}
<dt>${category_name}</dt>
<dd>[Assets](./docs/infrastructure/${category_name}/assets.md) and [Variables](./docs/infrastructure/${category_name}/variables.md)</dd>
<dd>
```yaml
${category_sample}
```
</dd>
%{ endfor ~}
</dl>

Each category has documentation for its assets and for its variables.

The _assets_ are the already provisioned resources for the category.

You can review any parameter for a provisioned resource from there.

The _variables_ are the parameters available to configure for a resource in the category.


