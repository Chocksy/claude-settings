Here are four practical ways to get rid of the constant prompt, ranked from “keep everything secure & native” → “quick-and-dirty until you’ve got time to revisit”.

────────────────────────────────────────
1. Stay with Keychain – but store the token **with a permissive ACL**

The line that writes the token still uses `-U`, which **updates** the old record and preserves the restrictive ACL that blocks unattended reads.  
Replace the write completely, deleting first and adding back with the **-A** (“any app may read”) flag:

```bash
# ~/.bashrc  (inside get_op_session)
security delete-generic-password -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" 2>/dev/null
security add-generic-password -A -s "$KEYCHAIN_SERVICE" -a "$KEYCHAIN_ACCOUNT" -w "$token"
```

After you add that:

```bash
# one-off
security delete-generic-password -s op-session -a default 2>/dev/null
# open a brand-new terminal twice:
# -> you should now see “Retrieved token … / Validating token …” and no sign-in.
```

Pros  
• still encrypted at rest, protected by macOS keychain  
• zero plaintext secrets anywhere  

Cons  
• session still expires after 30 min of inactivity (hard limit for manual `op signin`) – script will refresh automatically though.

────────────────────────────────────────
2. Skip tokens entirely – use the **desktop-app integration** with a long biometric timeout

Since you already enabled the integration, you can keep the desktop app unlocked for longer:

```bash
# ~/.bashrc – before you call op
export OP_BIOMETRIC_UNLOCK_TIMEOUT=$((12*60*60))  # 12 hours
```

Then drop the whole token-caching block and just run

```bash
eval "$(op inject -i "$HOME/dev.env")"
```

The first `op` in every macOS session asks for Touch ID once, then re-uses the app-level unlock for the next 12 h.  
(See “app integration security” section of the docs [1Password CLI reference](https://developer.1password.com/docs/cli/reference/#1password-app-integration-security)).

Pros  
• no custom code, no extra secrets  
• security handled by 1Password app  
Cons  
• still one Touch ID per login session (but not every new tab)  
• depends on desktop app being running & unlocked

────────────────────────────────────────
3. File-based session cache (the **PurpleBooth + sops** wrapper)

Drop-in wrapper from the gist <https://gist.github.com/PurpleBooth/7e27f5c439a2cb973bbf73bdd714ff88>:  

1. Save it as `~/bin/opwrap`, `chmod +x`.  
2. Install `sops` (brew install sops) – it encrypts the YAML cache with your macOS key.  
3. Add an alias so every `op` call goes through the wrapper:

```bash
alias op='opwrap'        # add to ~/.bashrc or ~/.zshrc
```

The wrapper:

• keeps the raw session in  
  `~/Library/Caches/wrapper-1password/session-token.yaml` (encrypted)  
• transparently refreshes when `op list vaults` returns “not signed in”.

Pros  
• cross-platform (works the same on CI or Linux servers)  
• no Touch ID after the first run  
Cons  
• extra dependency (`sops`)  
• still a 30 min idle limit → wrapper silently re-signs in when needed  
• small delay on every `op` call (wrapper + sops decrypt)

────────────────────────────────────────
4. Generate a **static dev.env** and source it

If you only need the secrets for local dev and security isn’t a concern for a while:

```bash
# one-off refresh script
op inject -i "$HOME/dev.env" -o "$HOME/dev.env.cached"
```

In your shell start-up:

```bash
if [ -f "$HOME/dev.env.cached" ]; then
  set -o allexport
  source "$HOME/dev.env.cached"
  set +o allexport
else
  echo "⚠️  $HOME/dev.env.cached missing. Run refresh script."
fi
```

Pros  
• zero external tooling; instant shell start-up  
Cons  
• **all secrets sit unencrypted on disk** – rotate them when you switch back  
• you must remember to regenerate after every secret change in 1Password

────────────────────────────────────────
Recommendation
• Try option 1 (correct ACL) – it gives you exactly what you wanted with minimal change.  
• If you’d rather rely on the desktop app, option 2 is simplest.  
• Only fall back to 3 / 4 if the above still doesn’t meet your workflow.

Let me know which path you’d like to implement and I’ll wire up the exact code changes. 🎉