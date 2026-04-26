#!/usr/bin/env node
"use strict";

const { spawnSync } = require("node:child_process");
const { join } = require("node:path");
const readline = require("node:readline");

const python = process.env.PYTHON || process.env.PYTHON3 || "python3";
const wrapperPath = join(__dirname, "..", "harness_deploy.py");
const env = {
  ...process.env,
  PYTHONDONTWRITEBYTECODE: process.env.PYTHONDONTWRITEBYTECODE || "1",
};

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
`);
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

1. Diagnose current install
2. Verify current install
3. Show update dry-run plan
4. Apply update after explicit confirmation
5. Show CLI help
6. Exit
`);
      const choice = (await question(rl, "Select an action: ")).trim().toLowerCase();

      if (choice === "1") {
        runWrapper(["diagnose", "--backend", "agents", "--json"]);
        await pause(rl);
      } else if (choice === "2") {
        runWrapper(["verify", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "3") {
        runWrapper(["update", "--backend", "agents"]);
        await pause(rl);
      } else if (choice === "4") {
        const confirmation = (await question(
          rl,
          "Type yes to apply update via prune --all -> check_paths_exist -> install -> verify: ",
        )).trim();
        if (confirmation === "yes") {
          runWrapper(["update", "--backend", "agents", "--yes"]);
        } else {
          console.log("Update cancelled.");
        }
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
