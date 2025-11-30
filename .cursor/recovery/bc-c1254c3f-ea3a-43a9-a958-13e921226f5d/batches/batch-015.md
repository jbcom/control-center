# Messages 141-150

## [141] 🤖 ASSISTANT

Now let me read the generator to fully understand the stacking merge pattern:

---

## [142] 🤖 ASSISTANT

I now understand the stacking merge pattern:

**targets.yaml shows inheritance:**
```yaml
Serverless_Stg:
  imports:
    - analytics
    - analytics-engineers

Serverless_Prod:
  - Serverless_Stg    # Inherits ALL from Stg

livequery_demos:
  - Serverless_Prod   # Cascading inheritance
```

Let me wait for CI and then proceed:

---

## [143] 🤖 ASSISTANT

All CI checks passed. Let me merge PR #168:

---

## [144] 🤖 ASSISTANT

PR #168 merged! Let me update to main and watch the release:

---

## [145] 🤖 ASSISTANT

CI is running on main. Now let me create the terraform-modules removal PR - removing the secrets methods since they're now in vendor-connectors:

---

## [146] 🤖 ASSISTANT

These modules aren't used within terraform-modules itself - they're only used by terraform-aws-secretsmanager. Let me create the removal branch:

---

## [147] 🤖 ASSISTANT

Let me replace these methods with deprecation notices rather than fully removing them (safer for transition):

---

## [148] 👤 USER

Yeah when you RUN tm_cli terraform_modules it autocleans

---

## [149] 🤖 ASSISTANT

Got it! So I just need to deprecate the methods and `tm_cli terraform_modules` will clean up the generated modules automatically. Let me finish the other 3 methods:

---

## [150] 👤 USER

Well if by depreciate you mean remove them with a chainsaw then yes

---

