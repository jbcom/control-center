# Messages 231-240

## [231] 🤖 ASSISTANT

Now let me check the generator/main.tf to find the workflow config:

---

## [232] 🤖 ASSISTANT

Now I understand the structure. I need to:
1. Add `use_oidc_auth = false` to the workflow config in `generator/main.tf`
2. Update the actual workflow file to use access keys

Let me make both changes:

---

## [233] 🤖 ASSISTANT

Now update the workflow file to use access keys instead of OIDC:

---

## [234] 🤖 ASSISTANT

Now update the secrets job too:

---

## [235] 🤖 ASSISTANT

Now let me commit and push these changes:

---

## [236] 🤖 ASSISTANT

Pushed. Now let me trigger the workflow to test it:

---

## [237] 🤖 ASSISTANT

The issue is clear: `EXTERNAL_CI_ACCESS_KEY` and `EXTERNAL_CI_SECRET_KEY` are empty! The safety valve workflow was cancelled. Let me check what secrets exist in the org:

---

## [238] 🤖 ASSISTANT

`EXTERNAL_CI_SECRET_KEY` is missing! Let me check the source org:

---

## [239] 🤖 ASSISTANT

The safety valve was cancelled halfway through. Let me run it again to complete the sync:

---

## [240] 🤖 ASSISTANT

The workflow was cancelled. Let me check the logs to see what happened:

---

