#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const { existsSync, readFileSync } = require("node:fs");
const { dirname, join } = require("node:path");
const readline = require("node:readline");

const python = "python3";
const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const env = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE || "1",
};
const packageVersionFallbackMaxDepth = 20;

function tryReadPackageVersionAt(candidate) {
  try {
    const packageMetadata = JSON.parse(readFileSync(candidate, "utf8"));
    if (packageMetadata.name === "aw-installer" && packageMetadata.version) {
      return packageMetadata.version;
    }
    return "";
  } catch (error) {
    throw new Error(`failed to read package metadata at ${candidate}: ${error.message}`);
  }
}

function printHelp() {
  console.log(`usage: aw-installer [tui|<deploy-mode>] [options]

Run AW Harness installer commands through the stable distribution wrapper.
Deploy modes delegate to harness_deploy.py and preserve adapter_deploy.py
semantics.

commands:
  tui                         open the interactive installer shell
  diagnose --backend agents   print a read-only deploy status summary
  verify --backend agents     run strict read-only deploy verification
  install --backend agents    install the current source payload
  update --backend agents     print an update dry-run plan
  update --backend agents --yes
                              apply the explicit update plan
  prune --all --backend agents
                              remove managed installs for the backend
  check_paths_exist --backend agents
                              scan write paths before install

options:
  -h, --help                  show this help message
  -V, --version               show package version
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

function runWrapper(args) {
  const result = spawnSync(python, [wrapperPath, ...args], {
    env,
    stdio: "inherit",
  });

  if (result.error) {
    console.error(`aw-installer failed to start ${python}: ${result.error.message}`);
    return 1;
  }

  if (result.signal) {
    console.error(`aw-installer terminated by signal ${result.signal}`);
    return 1;
  }

  return result.status === null ? 1 : result.status;
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
  const diagnoseStatus = runWrapper(["diagnose", "--backend", "agents", "--json"]);
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
  const dryRunStatus = runWrapper(["update", "--backend", "agents"]);
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
    runWrapper(["update", "--backend", "agents", "--yes"]);
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
        runWrapper(["diagnose", "--backend", "agents", "--json"]);
        await pause(rl);
      } else if (choice === "3") {
        runWrapper(["verify", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "4") {
        runWrapper(["update", "--backend", "agents"]);
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

  return runWrapper(args);
}

main()
  .then((status) => {
    process.exit(status);
  })
  .catch((error) => {
    console.error(`aw-installer failed: ${error.message}`);
    process.exit(1);
  });
