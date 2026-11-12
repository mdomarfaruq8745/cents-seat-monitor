CEnT-S FREE CLOUD MONITOR — GITHUB ACTIONS + TELEGRAM
=====================================================

WHAT THIS VERSION DOES
----------------------
- Runs in GitHub Actions cloud; your Windows PC can be off.
- Checks the public CISIA CEnT-S calendar on a 5-minute schedule.
- Sends Telegram alerts for newly available sessions and increased seat counts.
- Saves previous seat data in state.json and commits changes to this repository.
- Can also be started manually from the GitHub Actions tab.

IMPORTANT LIMITATIONS
---------------------
GitHub scheduled workflows have a minimum interval of 5 minutes, not 120 seconds.
GitHub warns scheduled runs can be delayed during high load and some queued runs
may be dropped. This is therefore not a guaranteed real-time/24-hour uptime service.
For a public repository, schedules may be disabled after 60 days without repository
activity. Visit the repository and make occasional changes/check the workflow.
Public repositories using standard GitHub-hosted runners have free Actions usage.
Keep the repository public if you want the public-repository free-runner terms;
never commit your Telegram token. GitHub Secrets protect the token.

STEP 1 — CREATE A TELEGRAM BOT
------------------------------
1. In Telegram, open @BotFather.
2. Send /newbot and follow the instructions.
3. Copy the bot token and keep it secret.
4. Open your new bot and press Start/send /start.

STEP 2 — GET YOUR CHAT ID
-------------------------
Open this URL in a browser, replacing YOUR_TOKEN:
https://api.telegram.org/botYOUR_TOKEN/getUpdates

Find "chat":{"id":123456789...}. That number is your chat ID.
If no update appears, send /start to your bot again and refresh.
Do not share the URL; it contains your token.

STEP 3 — CREATE A GITHUB REPOSITORY
-----------------------------------
1. Sign in at https://github.com/
2. Click +, then New repository.
3. Name it: cents-seat-monitor
4. Choose Public to use the free public-repository Actions allowance.
5. Create the repository.

STEP 4 — UPLOAD THESE FILES
---------------------------
Upload the extracted contents of this ZIP to the repository's default branch.
Make sure the folder structure is preserved:

monitor.py
requirements.txt
state.json             (will be created by the first successful run)
.github/workflows/monitor.yml

On GitHub, use Add file > Upload files. To create the workflow path, create
the folders .github/workflows and upload monitor.yml inside it. The ZIP already
contains the correct folders.

STEP 5 — ADD TELEGRAM SECRETS
-----------------------------
In your repository:
Settings > Secrets and variables > Actions > New repository secret

Create these TWO secrets:
- TELEGRAM_BOT_TOKEN = token from BotFather
- TELEGRAM_CHAT_ID = your Telegram chat ID

Do not put secrets in source code or state.json.

STEP 6 — ENABLE AND TEST
------------------------
1. Open the repository's Actions tab.
2. If asked, enable workflows.
3. Select "CEnT-S seat monitor".
4. Click Run workflow > Run workflow for an immediate test.
5. Wait for the run to finish and check Telegram.
6. After the first run, state.json is created and committed. Future runs compare
   against that saved history.

The scheduled workflow is set to run every 5 minutes at minute 2, 7, 12, ... 57
UTC. GitHub can delay or drop scheduled runs, so actual intervals may be longer.
The workflow file must be on the default branch.

HOW HISTORY WORKS
-----------------
state.json contains the latest known availability and seat count for each exam
session. Each successful run commits changes to state.json, so later runs can
detect newly released seats and seat increases. Do not delete this file if you
want to preserve the history.

HOW TO CHECK IT
---------------
Repository > Actions shows each check and its logs.
Repository > state.json shows the last saved seat snapshot.
The CISIA calendar remains the source of truth:
https://testcisia.it/calendario.php?tolc=cents&l=gb&lingua=inglese

SECURITY
--------
- Never publish your bot token or getUpdates URL.
- If a token leaks, revoke it through @BotFather and create a new one.
- A public repository exposes the Python source and seat history, but GitHub
  Actions secrets are not exposed in normal workflow logs unless you print them.
- This is an independent monitor, not an official CISIA service.
- It does not log into CISIA, bypass CAPTCHA, reserve a seat, or guarantee
  availability at the moment you open the booking page.
