@echo off
REM LlamaForge fork updater.
REM Syncs your fork (fork) with the author's repo (origin) while keeping your changes.
REM
REM Usage:
REM   update_fork.cmd          - sync fork with upstream (default: merge)
REM   update_fork.cmd rebase   - sync fork with upstream (rebase your changes on top)
setlocal enabledelayedexpansion

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

echo.
echo === LlamaForge Fork Updater ===
echo.

REM Check remotes exist
git remote get-url origin >nul 2>nul
if errorlevel 1 (
    echo [error] 'origin' remote not found. This doesn't look like the LlamaForge repo.
    goto :end
)
git remote get-url fork >nul 2>nul
if errorlevel 1 (
    echo [error] 'fork' remote not found. Run: git remote add fork https://github.com/Alihkhawaher/LlamaForge.git
    goto :end
)

REM Save current branch
for /f "tokens=*" %%b in ('git branch --show-current') do set "CURRENT_BRANCH=%%b"
echo Current branch: %CURRENT_BRANCH%

REM 1. Fetch latest from both remotes
echo.
echo [1/4] Fetching upstream (origin)...
git fetch origin
if errorlevel 1 (
    echo [error] fetch origin failed
    goto :end
)

echo [2/4] Fetching your fork (fork)...
git fetch fork
if errorlevel 1 (
    echo [error] fetch fork failed
    goto :end
)

REM 2. Switch to master and merge upstream
echo.
echo [3/4] Updating local master from upstream...
git checkout master
if errorlevel 1 (
    echo [error] checkout master failed
    goto :end
)
git merge origin/master --ff-only
if errorlevel 1 (
    echo [warn] fast-forward failed, trying merge...
    git merge origin/master
    if errorlevel 1 (
        echo [error] merge failed - resolve conflicts manually
        goto :end
    )
)
echo master updated.

REM 3. Update current working branch if not master
if not "%CURRENT_BRANCH%"=="master" (
    echo.
    echo [4/4] Updating branch '%CURRENT_BRANCH%' with upstream changes...
    git checkout "%CURRENT_BRANCH%"
    if "%~1"=="rebase" (
        echo Rebasing on master...
        git rebase master
        if errorlevel 1 (
            echo [error] rebase failed - resolve conflicts, then: git rebase --continue
            goto :end
        )
    ) else (
        echo Merging master into %CURRENT_BRANCH%...
        git merge master
        if errorlevel 1 (
            echo [error] merge failed - resolve conflicts manually
            goto :end
        )
    )
) else (
    echo [4/4] Already on master, skipping branch update.
)

REM 4. Push to fork
echo.
echo Pushing to fork...
git push fork "%CURRENT_BRANCH%"
if errorlevel 1 (
    echo [warn] push failed - you may need: git push fork "%CURRENT_BRANCH%" --force
    goto :end
)

echo.
echo === Done! Fork synced with upstream. ===
echo Your PR (if open) has been updated automatically.
echo.

:end
endlocal