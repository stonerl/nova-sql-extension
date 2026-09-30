/* LanguageClient wrapper for the bundled sqls language server. */

const SQL_SYNTAXES = [
  "sql-generic",
  "mysql",
  "mariadb",
  "postgresql",
  "tsql",
  "plsql",
  "sqlite",
  "bigquery",
  "flinksql",
  "hiveql",
  "n1ql",
  "redshift",
  "singlestore",
  "snowflake",
  "sparksql",
  "sqlpl",
  "trino",
];

const PREF_PREFIX = "stonerl.sql.";

const RESTART_BASE_DELAY_MS = 1000;
const RESTART_MAX_DELAY_MS = 30000;
const RESTART_STABLE_UPTIME_MS = 60000;

let sqlsServer = null;

class SqlsLanguageServer {
  constructor() {
    this.languageClient = null;
    this.didStopDisposable = null;
    this.restartAttempts = 0;
    this.restartTimer = null;
    this.startedAt = 0;
  }

  start() {
    if (this.languageClient) {
      return;
    }

    const binaryPath = this.configuredBinaryPath();
    if (!nova.fs.access(binaryPath, nova.fs.F_OK)) {
      console.error("sqls binary not found at:", binaryPath);
      return;
    }

    const serverOptions = {
      path: binaryPath,
      args: [],
    };

    const clientOptions = {
      syntaxes: SQL_SYNTAXES,
    };

    const client = new LanguageClient(
      "sqls",
      "SQL Language Server",
      serverOptions,
      clientOptions,
    );

    // Register before start(): launch failures are reported
    // asynchronously via onDidStop, not thrown synchronously.
    this.didStopDisposable = client.onDidStop((err) => {
      if (this.languageClient !== client) return;

      this.languageClient = null;
      if (err) {
        console.error("sqls stopped unexpectedly:", err);
        this.scheduleRestart();
      }
    });

    client.start();
    this.startedAt = Date.now();
    console.log("Starting sqls language server:", binaryPath);
    nova.subscriptions.add(client);
    this.languageClient = client;
  }

  stop() {
    if (this.restartTimer) {
      clearTimeout(this.restartTimer);
      this.restartTimer = null;
    }
    if (this.didStopDisposable) {
      this.didStopDisposable.dispose();
      this.didStopDisposable = null;
    }
    this.restartAttempts = 0;

    if (this.languageClient) {
      this.languageClient.stop();
      nova.subscriptions.remove(this.languageClient);
      this.languageClient = null;
      console.log("sqls language server stopped");
    }
  }

  restart() {
    this.stop();
    this.start();
  }

  scheduleRestart() {
    if (this.restartTimer) return;

    const uptime = Date.now() - this.startedAt;
    if (uptime > RESTART_STABLE_UPTIME_MS) {
      this.restartAttempts = 0;
    }

    const delay = Math.min(
      RESTART_BASE_DELAY_MS * 2 ** this.restartAttempts,
      RESTART_MAX_DELAY_MS,
    );
    this.restartAttempts += 1;

    console.warn(
      `Restarting sqls in ${delay}ms (attempt ${this.restartAttempts})`,
    );
    if (nova.inDevMode() && this.restartAttempts === 1) {
      nova.workspace.showInformativeMessage(
        "SQL language server stopped unexpectedly. Restarting…",
      );
    }

    this.restartTimer = setTimeout(() => {
      this.restartTimer = null;
      if (!nova.config.get(PREF_PREFIX + "enable-language-server")) return;
      if (this.languageClient) return;
      this.start();
    }, delay);
  }

  configuredBinaryPath() {
    const customPath = nova.config.get(
      PREF_PREFIX + "sqls-binary-path",
      "string",
    );
    return customPath || nova.extension.path + "/Executables/sqls";
  }
}

exports.activate = function () {
  const server = new SqlsLanguageServer();
  sqlsServer = server;

  // Respect the enable-language-server preference; start once per editor
  // opening like most Nova LSP extensions do (activation events already
  // gate on SQL syntaxes).
  if (nova.config.get(PREF_PREFIX + "enable-language-server")) {
    server.start();
  } else {
    console.log("SQL language server disabled by preference");
  }

  nova.config.onDidChange(PREF_PREFIX + "enable-language-server", (enabled) => {
    if (enabled) {
      server.start();
    } else {
      server.stop();
    }
  });

  nova.config.onDidChange(PREF_PREFIX + "sqls-binary-path", () => {
    if (nova.config.get(PREF_PREFIX + "enable-language-server")) {
      server.restart();
    }
  });

  nova.commands.register("restartLanguageServer", () => {
    server.restart();
  });

  nova.commands.register("showServerInfo", async () => {
    const enabled = nova.config.get(PREF_PREFIX + "enable-language-server");
    const path = server.configuredBinaryPath();
    const exists = nova.fs.access(path, nova.fs.F_OK);
    const running = !!(server.languageClient && server.languageClient.running);
    await nova.workspace.showInformativeMessage(
      [
        `Language server: ${enabled ? "enabled" : "disabled"}`,
        `Server state: ${running ? "running" : "stopped"}`,
        `Binary: ${path}`,
        exists ? "Binary found." : "Binary NOT found — check the path.",
      ].join("\n"),
    );
  });
};

exports.deactivate = function () {
  // Explicit stop before Nova disposes nova.subscriptions.
  if (sqlsServer) {
    sqlsServer.stop();
    sqlsServer = null;
  }
};
