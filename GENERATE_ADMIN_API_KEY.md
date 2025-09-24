# 🔑 How to Generate `ADMIN_API_KEY`

Currently, the `ADMIN_API_KEY` must be generated manually. You can create it on your computer by generating a 32-character hash and then storing it manually in the `.env` file or export it manually when running the script.

## On Linux / Mac (bash)

```bash
openssl rand -hex 16
```

This will generate a random 32-character hexadecimal string that you can copy and paste into your `.env` file as:

```env
ADMIN_API_KEY=your-generated-hash
```

## On Windows (PowerShell)

```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | % {[char]$_})
```

This will generate a random 32-character alphanumeric string. Copy and paste it into your `.env` file the same way.

---

**⚠️ Note:** The `ADMIN_API_KEY` is the same for both the main application and the script.
