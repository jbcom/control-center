# Messages 121-130

## [121] 🤖 ASSISTANT

Understood! Since this functionality is ONLY for secrets merging/syncing, we can completely remove it from terraform-modules once vendor-connectors has it all. Let me finish porting the complete Vault `get_secret()` with the matchers logic and path handling:

---

## [122] 🤖 ASSISTANT

Now let me also check what we have in extended-data-types for the `is_nothing` utility - this should be a shared function:

---

## [123] 🤖 ASSISTANT

`is_nothing` already exists in `extended-data-types`! Let me update both connectors to use it instead of duplicating:

---

## [124] 🤖 ASSISTANT

Now update Vault connector:

---

## [125] 🤖 ASSISTANT

Now let me add the `deque` import at the module level:

---

## [126] 🤖 ASSISTANT

Now let me run linting to check for any issues:

---

## [127] 🤖 ASSISTANT

Let me verify the final files and then commit:

---

## [128] 🤖 ASSISTANT

I see there's a duplicate `from collections import deque` in `list_secrets`. Let me fix that:

---

## [129] 🤖 ASSISTANT

Now let me commit the changes:

---

## [130] 👤 USER

Just fix your environment and add uv

---

