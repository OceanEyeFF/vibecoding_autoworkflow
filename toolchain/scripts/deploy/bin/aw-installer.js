#!/usr/bin/env node
"use strict";

const { spawn } = require("node:child_process");
const { existsSync, readFileSync } = require("node:fs");
const { dirname, join } = require("node:path");
const readline = require("node:readline");

const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const defaultWrapperTimeoutMs = 300_000;
const wrapperTimeoutMs = readWrapperTimeoutMs();
const env = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE || "1",
};
const packageVersionFallbackMaxDepth = 20;

function readWrapperTimeoutMs() {
  const parsedTimeout = Number.parseInt(
    process.env.AW_INSTALLER_WRAPPER_TIMEOUT_MS || `${defaultWrapperTimeoutMs}`,
    10,
  );
  if (Number.isFinite(parsedTimeout) && parsedTimeout > 0) {
    return parsedTimeout;
  }
  return defaultWrapperTimeoutMs;
}

function pythonCandidates() {
  if (process.platform === "win32") {
    return [
      { command: "py", args: ["-3"] },
      { command: "python", args: [] },
      { command: "python3", args: [] },
    ];
  }
  return [
    { command: "python3", args: [] },
    { command: "python", args: [] },
  ];
}

function formatPythonCandidate(candidate) {
  return [candidate.command, ...candidate.args].join(" ");
}

function tryReadPackageVersionAt(candidate) {
  try {
    const packageMetadata = JSON.parse(readFileSync(candidate, "utf8"));
    if (packageMetadata.name === "aw-installer" && packageMetadata.version) {
      return packageMetadata.version;
    }
    return "";
  } catch (error) {
    return "";
  }
}

function printHelp() {
  console.log(`usage: aw-installer [tui|<deploy-mode>] [options]

Run AW Harness installer commands through the stable distribution wrapper.
Deploy modes delegate to harness_deploy.py and preserve adapter_deploy.py
semantics.

commands:
  tui                         open the interactive installer shell
  diagnose --backend agents|claude
                              print a read-only deploy status summary
  verify --backend agents|claude
                              run strict read-only deploy verification
  install --backend agents|claude
                              install the current source payload
  update --backend agents|claude
                              print an update dry-run plan
  update --backend agents --yes
                              apply the explicit update plan
  update --backend agents --source github --github-ref master
                              update from the approved GitHub source archive
  prune --all --backend agents|claude
                              remove managed installs for the backend
  check_paths_exist --backend agents|claude
                              scan write paths before install

options:
  -h, --help                  show this help message
  -V, --version               show package version
  --source package|github     select package-local or GitHub update source
  --agents-root PATH          override the managed agents skills target root
  --claude-root PATH          override the managed Claude skills target root
  --github-repo OWNER/REPO    GitHub source repository for --source github
                              defaults from AW_INSTALLER_GITHUB_REPO,
                              GITHUB_REPOSITORY, then upstream repo
  --github-ref REF            GitHub branch/ref for --source github
`);
}

function readPackageVersion() {
  const knownPackagePaths = [
    join(__dirname, "..", "..", "..", "..", "package.json"),
    join(__dirname, "..", "package.json"),
  ];
  for (const candidate of knownPackagePaths) {
    if (!existsSync(candidate)) {
      continue;
    }
    const packageVersion = tryReadPackageVersionAt(candidate);
    if (packageVersion) {
      return packageVersion;
    }
  }

  let current = __dirname;
  for (let depth = 0; depth < packageVersionFallbackMaxDepth; depth += 1) {
    const candidate = join(current, "package.json");
    if (existsSync(candidate)) {
      const packageVersion = tryReadPackageVersionAt(candidate);
      if (packageVersion) {
        return packageVersion;
      }
    }

    const parent = dirname(current);
    if (parent === current) {
      throw new Error("could not find aw-installer package metadata");
    }
    current = parent;
  }
  throw new Error(
    `could not find aw-installer package metadata within ${packageVersionFallbackMaxDepth} parent directories`,
  );
}

function printVersion() {
  console.log(`aw-installer ${readPackageVersion()}`);
}

function runWrapperWithCandidate(args, candidate) {
  return new Promise((resolve) => {
    const abortController = new AbortController();
    // The child can emit both error and close; settle once and keep timeout reporting distinct.
    let timedOut = false;
    let settled = false;
    const finish = (status) => {
      if (settled) {
        return false;
      }
      settled = true;
      clearTimeout(timer);
      resolve(status);
      return true;
    };
    const timeoutSeconds = Math.ceil(wrapperTimeoutMs / 1000);
    const timer = setTimeout(() => {
      timedOut = true;
      abortController.abort();
    }, wrapperTimeoutMs);
    if (typeof timer.unref === "function") {
      timer.unref();
    }

    let child;
    try {
      child = spawn(candidate.command, [...candidate.args, wrapperPath, ...args], {
        env,
        signal: abortController.signal,
        stdio: "inherit",
      });
    } catch (error) {
      clearTimeout(timer);
      if (error.code === "ENOENT") {
        resolve({ status: 1, missing: true, error });
        return;
      }
      console.error(
        `aw-installer failed to start ${formatPythonCandidate(candidate)}: ${error.message}`,
      );
      resolve({ status: 1, missing: false, error });
      return;
    }

    child.on("error", (error) => {
      if (timedOut || error.name === "AbortError") {
        if (finish({ status: 1, missing: false })) {
          console.error(`aw-installer timed out after ${timeoutSeconds}s`);
        }
        return;
      }
      if (error.code === "ENOENT") {
        if (settled) {
          return;
        }
        settled = true;
        clearTimeout(timer);
        resolve({ status: 1, missing: true, error });
        return;
      }
      if (!finish({ status: 1, missing: false, error })) {
        return;
      }
      console.error(
        `aw-installer failed to start ${formatPythonCandidate(candidate)}: ${error.message}`,
      );
    });
    child.on("close", (code, signal) => {
      if (timedOut) {
        if (finish({ status: 1, missing: false })) {
          console.error(`aw-installer timed out after ${timeoutSeconds}s`);
        }
        return;
      }
      if (signal) {
        if (!finish({ status: 1, missing: false })) {
          return;
        }
        console.error(`aw-installer terminated by signal ${signal}`);
        return;
      }
      finish({ status: code === null ? 1 : code, missing: false });
    });
  });
}

async function runWrapper(args) {
  const missingCandidates = [];
  for (const candidate of pythonCandidates()) {
    const result = await runWrapperWithCandidate(args, candidate);
    if (result.missing) {
      missingCandidates.push(formatPythonCandidate(candidate));
      continue;
    }
    return result.status;
  }
  console.error(
    `aw-installer failed to start Python; tried ${missingCandidates.join(", ")}`,
  );
  return 1;
}

function question(rl, prompt) {
  return new Promise((resolve) => {
    rl.question(prompt, resolve);
  });
}

async function pause(rl) {
  await question(rl, "\nPress Enter to return to the installer menu...");
}

async function runGuidedUpdateFlow(rl) {
  console.log("\nGuided update flow");
  console.log("Step 1: Diagnose current agents install.");
  const diagnoseStatus = await runWrapper(["diagnose", "--backend", "agents", "--json"]);
  if (diagnoseStatus !== 0) {
    console.log("Diagnose failed; update may not succeed as expected.");
    const proceed = (await question(
      rl,
      "Continue with update dry-run anyway? Type yes to continue: ",
    )).trim();
    if (proceed !== "yes") {
      console.log("Update cancelled.");
      await pause(rl);
      return;
    }
  }

  console.log("\nStep 2: Review update dry-run plan.");
  const dryRunStatus = await runWrapper(["update", "--backend", "agents"]);
  if (dryRunStatus !== 0) {
    console.log("Update plan failed; not applying.");
    await pause(rl);
    return;
  }

  const confirmation = (await question(
    rl,
    "Step 3: Type yes to apply update via prune --all -> check_paths_exist -> install -> verify: ",
  )).trim();
  if (confirmation === "yes") {
    console.log("\nStep 4: Applying update and running strict verify.");
    await runWrapper(["update", "--backend", "agents", "--yes"]);
  } else {
    console.log("Update cancelled.");
  }
  await pause(rl);
}

async function runTui() {
  if (!process.stdin.isTTY || !process.stdout.isTTY) {
    console.error("aw-installer tui requires an interactive terminal.");
    return 1;
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  try {
    while (true) {
      console.log(`
AW Installer
Backend: agents

1. Guided update flow
2. Diagnose current install
3. Verify current install
4. Show update dry-run plan
5. Show CLI help
6. Exit
`);
      const choice = (await question(rl, "Select an action: ")).trim().toLowerCase();

      if (choice === "1") {
        await runGuidedUpdateFlow(rl);
      } else if (choice === "2") {
        await runWrapper(["diagnose", "--backend", "agents", "--json"]);
        await pause(rl);
      } else if (choice === "3") {
        await runWrapper(["verify", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "4") {
        await runWrapper(["update", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "5") {
        printHelp();
        await pause(rl);
      } else if (choice === "6" || choice === "q" || choice === "quit" || choice === "exit") {
        return 0;
      } else {
        console.log("Unknown selection.");
      }
    }
  } finally {
    rl.close();
  }
}

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    if (process.stdin.isTTY && process.stdout.isTTY) {
      return runTui();
    }
    printHelp();
    return 0;
  }

  if (args[0] === "--help" || args[0] === "-h") {
    printHelp();
    return 0;
  }

  if (args[0] === "--version" || args[0] === "-V") {
    printVersion();
    return 0;
  }

  if (args[0] === "tui") {
    return runTui();
  }

  return await runWrapper(args);
}

main()
  .then((status) => {
    process.exit(status);
  })
  .catch((error) => {
    console.error(`aw-installer failed: ${error.message}`);
    process.exit(1);
  });
